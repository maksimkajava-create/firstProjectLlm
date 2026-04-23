# routers/auth.py
"""
Роутер: регистрация и авторизация (/auth)
"""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schemas import UserRegister, TokenResponse, UserResponse, ResetPasswordRequest
from services.crud.user import create_user, reset_password


from database.connection import get_db
from models.entities import User
from schemas import UserRegister, TokenResponse, UserResponse
from services.crud.user import create_user
from auth_utils import create_access_token

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    Создаёт нового пользователя.
    - Проверяет уникальность email.
    - Пароль хэшируется (SHA-256) перед сохранением.
    """
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )
    user = create_user(db, email=data.email, password=data.password)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Авторизация (получение JWT-токена)",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Принимает email (в поле username) и пароль.
    Возвращает JWT access-токен.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    password_hash = hashlib.sha256(
        form_data.password.encode("utf-8")
    ).hexdigest()
    if user.password_hash != password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token)

@router.post(
    "/reset-password",
    summary="Сброс пароля (упрощённый)",
)
def reset_pwd(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Упрощённый сброс пароля"""
    try:
        reset_password(db, email=data.email, new_password=data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"message": "Пароль успешно изменён"}
