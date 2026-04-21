# routers/balance.py
"""
Роутер: работа с балансом (/balance)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import DepositRequest, BalanceResponse
from services import process_transaction
from auth_utils import get_current_user

router = APIRouter(prefix="/balance", tags=["Баланс"])


@router.get(
    "/",
    response_model=BalanceResponse,
    summary="Получить текущий баланс",
)
def get_balance(current_user: User = Depends(get_current_user)):
    """Возвращает текущий баланс авторизованного пользователя."""
    return BalanceResponse(balance=current_user.account.balance)


@router.post(
    "/deposit",
    response_model=BalanceResponse,
    summary="Пополнить баланс",
)
def deposit(
    data: DepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Пополняет баланс на указанную сумму.
    Возвращает обновлённый баланс.
    """
    process_transaction(
        db, user=current_user, amount=data.amount, t_type="credit"
    )
    db.refresh(current_user)
    return BalanceResponse(balance=current_user.account.balance)
