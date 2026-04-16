from sqlalchemy.orm import Session
from sqlalchemy import desc
import hashlib

from models import User, Transaction, MLTask, MLModelConfig

def create_user(db: Session, email: str, password: str, balance: float = 0.0):
    """Создание пользователя"""
    hashed_pwd = hashlib.sha256(password.encode('utf-8')).hexdigest()
    db_user = User(email=email, password_hash=hashed_pwd, balance=balance)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def process_transaction(db: Session, user: User, amount: float, t_type: str, task_id: int = None):
    """Пополнение или списание"""
    if t_type == "debit":
        if user.balance < amount:
            raise ValueError("Недостаточно средств на балансе")
        user.balance -= amount
    elif t_type == "credit":
        user.balance += amount
    else:
        raise ValueError("Неверный тип транзакции")

    new_txn = Transaction(
        user_id=user.id, 
        amount=amount, 
        transaction_type=t_type, 
        task_id=task_id
    )
    db.add(new_txn)
    db.commit() 
    return new_txn

def get_user_history(db: Session, user_id: int):
    """Получение истории предиктов (сортировка по дате)"""
    history = db.query(MLTask).filter(MLTask.user_id == user_id)\
                .order_by(desc(MLTask.created_at)).all()
    return history