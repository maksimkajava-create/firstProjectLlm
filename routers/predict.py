# routers/predict.py
"""
Роутер: ML-предсказания (/predict)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, MLModelConfig
from schemas import PredictRequest, PredictResponse
from services import run_prediction
from auth_utils import get_current_user

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
    3. Выполнить предсказание
    4. Списать стоимость с баланса
    5. Сохранить задачу и транзакцию в бд
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
    if current_user.balance < cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Недостаточно средств на балансе. "
                f"Требуется: {cost}, доступно: {current_user.balance}"
            ),
        )

    # 3-5 предсказание + списание + сохранение
    try:
        task = run_prediction(
            db, user=current_user, model=model, features=data.features
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return PredictResponse(
        task_id=task.id,
        status=task.status,
        output_data=task.output_data,
        cost=cost,
    )
