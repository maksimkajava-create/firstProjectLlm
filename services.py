"""
Сервисный слой — вся бизнес-логика в одном месте.
Контроллеры (роутеры) только вызывают эти функции.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
import hashlib
from models import User, Account, Transaction, MLTask, MLModelConfig

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
        user_id = db_user.id,
        balance = balance
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
        user.balance += amount
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

def execute_prediction(model_name: str, input_data: dict) -> dict:
    """
    Выполняет предсказание на основе имени модели.
    Логика имитации в SimpleClassifier: сумма признаков => 0 - A, иначе - B.
    """
    features = input_data.get("features", [])
    if model_name == "SimpleClassifier":
        total = sum(features)
        label = "A" if total >= 0 else "B"
        return {"label": label}
    raise ValueError(f"Неизвестная модель: {model_name}")


def run_prediction(
    db: Session,
    user: User,
    model: MLModelConfig,
    features: list,
) -> MLTask:
    """
    Полный цикл ML-предсказания:
    1. Выполнить предсказание
    2. Сохранить задачу в БД
    3. Списать стоимость с баланса пользователя
    """
    input_data = {"features": features}
    output_data = execute_prediction(model.name, input_data)

    task = MLTask(
        user_id=user.id,
        model_id=model.id,
        input_data=input_data,
        output_data=output_data,
        status="completed",
    )
    db.add(task)
    db.flush()  # получить task.id до коммита

    process_transaction(
        db,
        user=user,
        amount=model.cost_per_prediction,
        t_type="debit",
        task_id=task.id,
    )
    return task


def get_user_history(db: Session, user_id: int):
    """Получение истории ML-задач пользователя (сортировка по дате)"""
    history = (
        db.query(MLTask)
        .filter(MLTask.user_id == user_id)
        .order_by(desc(MLTask.created_at))
        .all()
    )
    return history


def get_user_transactions(db: Session, user_id: int):
    """Получение истории транзакций пользователя (сортировка по дате)"""
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(desc(Transaction.created_at))
        .all()
    )
    return transactions
