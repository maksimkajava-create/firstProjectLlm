"""
Pydantic-схемы для валидации запросов и ответов REST API.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

class UserRegister(BaseModel):
    """Схема регистрации нового пользователя"""
    email: str
    password: str = Field(min_length=8, description="Пароль (минимум 8 символов)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        if not pattern.match(v):
            raise ValueError("Некорректный формат email")
        return v


class TokenResponse(BaseModel):
    """Ответ с JWT-токеном после успешного логина"""
    access_token: str
    token_type: str = "bearer"

class AccountResponse(BaseModel):
    """Данные счёта"""
    id: int
    balance: float

    model_config = {"from_attributes": True}

class UserResponse(BaseModel):
    """Данные пользователя (публичная часть)"""
    id: int
    email: str
    role: str
    account: Optional[AccountResponse] = None
    model_config = {"from_attributes": True}

class DepositRequest(BaseModel):
    """Запрос на пополнение баланса"""
    amount: float = Field(gt=0, description="Сумма пополнения (больше нуля)")


class BalanceResponse(BaseModel):
    """Текущий баланс пользователя"""
    balance: float

class PredictRequest(BaseModel):
    """Запрос на ML-предсказание"""
    model_id: int = Field(description="ID ML-модели")
    features: List[float] = Field(description="Список признаков")

    @field_validator("features")
    @classmethod
    def features_not_empty(cls, v: List[float]) -> List[float]:
        if len(v) == 0:
            raise ValueError("Список признаков не может быть пустым")
        return v

class PredictResponse(BaseModel):
    """Результат ML-предсказания"""
    task_id: str #теперь строка
    status: str
    output_data: Optional[Dict[str, Any]] = None
    cost: float

    model_config = {"from_attributes": True}

class TaskStatusResponse(BaseModel):
    """Для проверки статуса задач по uuid"""
    task_id: str
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    created_at: datetime

class TaskHistoryItem(BaseModel):
    """Одна запись из истории ML-задач"""
    id: int
    task_uuid: Optional[str] = None
    model_id: int
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class TransactionHistoryItem(BaseModel):
    """Одна запись из истории транзакций"""
    id: int
    amount: float
    transaction_type: str
    task_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
