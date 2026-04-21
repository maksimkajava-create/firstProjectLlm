# routers/history.py 
"""
Роутер: история запросов и транзакций (/history)
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, MLTask
from schemas import TaskHistoryItem, TransactionHistoryItem
from services import get_user_history, get_user_transactions
from auth_utils import get_current_user

router = APIRouter(prefix="/history", tags=["История"])


@router.get(
    "/tasks",
    response_model=List[TaskHistoryItem],
    summary="История запросов",
)
def tasks_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает список выполненных задач пользователя
    (дата, статус, входные/выходные данные), сортировка по дате (DESC).
    """
    tasks = get_user_history(db, current_user.id)
    return tasks


@router.get(
    "/tasks/{task_id}",
    response_model=TaskHistoryItem,
    summary="Получить задачу по ID",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Возвращает задачу по task_id. Доступна только владельцу."""
    task = db.query(MLTask).filter(
        MLTask.id == task_id,
        MLTask.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена",
        )
    return task


@router.get(
    "/transactions",
    response_model=List[TransactionHistoryItem],
    summary="История транзакций",
)
def transactions_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает историю финансовых операций пользователя
    (пополнения и списания), сортировка по дате (DESC).
    """
    transactions = get_user_transactions(db, current_user.id)
    return transactions
