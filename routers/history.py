# routers/history.py 
"""
Роутер: история запросов и транзакций (/history)
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
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
