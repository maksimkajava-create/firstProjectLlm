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
