import hashlib
from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.entities import Account, Transaction, User


def create_user(
    db: Session,
    email: str,
    password: str,
    balance: float = 0.0,
) -> User:
    """Создание пользователя с хэшированием пароля"""
    hashed_pwd = hashlib.sha256(password.encode("utf-8")).hexdigest()
    db_user = User(
        email=email,
        password_hash=hashed_pwd
    )
    db.add(db_user)
    db.commit()
    db.flush()

    db_account = Account(
        user_id=db_user.id,
        balance=balance
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_user)
    return db_user


def process_transaction(
    db: Session,
    user: User,
    amount: float,
    t_type: str,
    task_id: int = None,
) -> Transaction:
    """Пополнение или списание баланса"""
    account = user.account
    if t_type == "debit":
        if account.balance < amount:
            raise ValueError("Недостаточно средств на балансе")
        account.balance -= amount
    elif t_type == "credit":
        account.balance += amount
    else:
        raise ValueError("Неверный тип транзакции")

    new_transaction = Transaction(
        user_id=user.id,
        amount=amount,
        transaction_type=t_type,
        task_id=task_id,
    )
    db.add(new_transaction)
    db.commit()
    return new_transaction


def get_user_transactions(db: Session, user_id: int):
    """История транзакций пользователя (DESC по дате)"""
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(desc(Transaction.created_at))
        .all()
    )


def reset_password(db: Session, email: str, new_password: str) -> User:
    """СБрос пароля"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("Пользователь с таким email не найден")
    user.password_hash = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(
    db: Session,
    user: User,
    email: str = None,
    old_password: str = None,
    new_password: str = None,
) -> User:
    """Обновления инфо пользователя"""
    if email and email != user.email:
        existing = db.query(User).filter(User.email == email, User.id != user.id).first()
        if existing:
            raise ValueError("Email уже занят другим пользователем")
        user.email = email

    if new_password:
        if not old_password:
            raise ValueError("Укажите текущий пароль для смены")
        old_hash = hashlib.sha256(old_password.encode("utf-8")).hexdigest()
        if user.password_hash != old_hash:
            raise ValueError("Неверный текущий пароль")
        user.password_hash = hashlib.sha256(new_password.encode("utf-8")).hexdigest()

    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session):
    return db.query(User).all()
