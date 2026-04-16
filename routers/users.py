#routers/users.py
"""
Роутер: данные пользователя (/users)
"""

from fastapi import APIRouter, Depends

from models import User
from schemas import UserResponse
from auth_utils import get_current_user

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получить профиль текущего пользователя",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Возвращает id, email, роль и баланс авторизованного пользователя."""
    return current_user
