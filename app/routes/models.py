from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from models.entities import User
from schemas import ModelResponse
from services.crud.ml_task import get_all_models
from auth_utils import get_current_user

router = APIRouter(prefix="/models", tags=["Модели"])


@router.get("/", response_model=List[ModelResponse], summary="Список доступных ML-моделей")
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение всех моделей"""
    return get_all_models(db)
