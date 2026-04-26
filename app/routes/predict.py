# routers/predict.py
"""
Роутер: ML-предсказания (/predict)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.entities import MLModelConfig, User
from schemas import PredictRequest, PredictResponse, TaskStatusResponse
from services.crud.ml_task import create_pending_task, get_task_by_uuid
from auth_utils import get_current_user
from services.rm.rm import publish_task


router = APIRouter(prefix="/predict", tags=["ML-предсказания"])


@router.post(
    "/",
    response_model=PredictResponse,
    summary="Выполнить ML-предсказание",
)
def predict(
    data: PredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cценарий:
    1. Найти ML-модель по id
    2. Проверить достаточность баланса
    3. Отправить задачу в очередь
    """
    # 1 найти модель
    model = (
        db.query(MLModelConfig)
        .filter(MLModelConfig.id == data.model_id)
        .first()
    )
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ML-модель с указанным id не найдена",
        )

    #2 проверить баланс
    cost = model.cost_per_prediction
    if current_user.account.balance < cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Недостаточно средств на балансе. "
                f"Требуется: {cost}, доступно: {current_user.account.balance}"
            ),
        )
    features = [float(f) for f in data.features] if data.features else None

    # 3 отправка задачи в очередь
    try:
        task = create_pending_task(
            db, user=current_user, model=model, features=features, prompt=data.prompt
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    message = {
        "task_id": task.task_uuid,
        "features": data.features,
        "prompt": data.prompt,
        "model": model.name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    try:
        publish_task(message)
    except Exception:
        task.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис обработки временно недоступен",
        )
    return PredictResponse(
        task_id=task.task_uuid,
        status=task.status,
        cost=model.cost_per_prediction,
    )

@router.get("/{task_uuid}", response_model=TaskStatusResponse)
def get_prediction_status(
    task_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение стататуса предсказания"""
    task = get_task_by_uuid(db, task_uuid=task_uuid, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена!"
        )
    
    return TaskStatusResponse(
        task_id=task.task_uuid,
        status=task.status,
        input_data=task.input_data,
        output_data=task.output_data,
        created_at=task.created_at
    )
