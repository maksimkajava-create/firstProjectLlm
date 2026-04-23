#routers/users.py
"""
Роутер: данные пользователя (/users)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from services.crud.user import update_user_profile
from models.entities import User
from schemas import UserResponse, UpdateProfileRequest
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

@router.patch("/me", response_model=UserResponse, summary="Обновить профиль")
def update_me(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Обновление юзера"""
    try:
        updated = update_user_profile(
            db,
            user=current_user,
            email=data.email,
            old_password=data.old_password,
            new_password=data.new_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return updated