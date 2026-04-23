import uuid
from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.entities import MLModelConfig, MLTask, Transaction, User


def execute_prediction(model_name: str, input_data: dict) -> dict:
    """
    Выполняет предсказание на основе имени модели.
    SimpleClassifier: сумма признаков >= 0 → A, иначе B.
    """
    features = input_data.get("features", [])
    if model_name == "SimpleClassifier":
        total = sum(features)
        label = "A" if total >= 0 else "B"
        return {"label": label}
    raise ValueError(f"Неизвестная модель: {model_name}")


def create_pending_task(
    db: Session,
    user: User,
    model: MLModelConfig,
    features: list,
) -> MLTask:
    task_uuid = str(uuid.uuid4())

    task = MLTask(
        task_uuid=task_uuid,
        user_id=user.id,
        model_id=model.id,
        input_data={"features": features},
        status="pending",
    )
    db.add(task)
    db.flush()

    account = user.account
    account.balance -= model.cost_per_prediction

    txn = Transaction(
        user_id=user.id,
        amount=model.cost_per_prediction,
        transaction_type="debit",
        task_id=task.id,
    )
    db.add(txn)
    db.commit()
    db.refresh(task)
    return task


def get_user_history(db: Session, user_id: int):
    """История ML-задач пользователя (DESC по дате)"""
    return (
        db.query(MLTask)
        .filter(MLTask.user_id == user_id)
        .order_by(desc(MLTask.created_at))
        .all()
    )


def get_task_by_id(db: Session, task_id: int, user_id: int):
    """ML-задача по числовому id и user_id"""
    return (
        db.query(MLTask)
        .filter(MLTask.id == task_id, MLTask.user_id == user_id)
        .first()
    )


def get_task_by_uuid(db: Session, task_uuid: str, user_id: int):
    """ML-задача по uuid и user_id"""
    return (
        db.query(MLTask)
        .filter(MLTask.task_uuid == task_uuid, MLTask.user_id == user_id)
        .first()
    )

def get_all_models(db: Session):
    return db.query(MLModelConfig).all()


def create_model(db: Session, name: str, description: str, cost: float) -> MLModelConfig:
    """Создание модели"""
    existing = db.query(MLModelConfig).filter(MLModelConfig.name == name).first()
    if existing:
        raise ValueError("Модель с таким именем уже существует")
    model = MLModelConfig(name=name, description=description, cost_per_prediction=cost)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model_id: int) -> None:
    """Удаление модели (для администратора)"""
    model = db.query(MLModelConfig).filter(MLModelConfig.id == model_id).first()
    if not model:
        raise ValueError("Модель не найдена")
    db.delete(model)
    db.commit()


def get_all_tasks(db: Session):
    return (
        db.query(MLTask)
        .order_by(desc(MLTask.created_at))
        .all()
    )
