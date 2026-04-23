from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from models.entities import User
from schemas import AdminUserItem, AdminTaskItem, ModelResponse, ModelCreateRequest
from services.crud.user import get_all_users
from services.crud.ml_task import get_all_tasks, get_all_models, create_model, delete_model
from auth_utils import get_admin_user

router = APIRouter(prefix="/admin", tags=["Администрирование"])


@router.get("/users", response_model=List[AdminUserItem], summary="Все пользователи")
def admin_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    users = get_all_users(db)
    result = []
    for u in users:
        result.append(AdminUserItem(
            id=u.id,
            email=u.email,
            role=u.role,
            balance=u.account.balance if u.account else 0.0,
        ))
    return result


@router.get("/tasks", response_model=List[AdminTaskItem], summary="Все задачи в системе")
def admin_tasks(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    return get_all_tasks(db)


@router.get("/models", response_model=List[ModelResponse], summary="Все модели")
def admin_models(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    return get_all_models(db)


@router.post(
    "/models",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать модель",
)
def admin_create_model(
    data: ModelCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    try:
        model = create_model(db, name=data.name, description=data.description, cost=data.cost_per_prediction)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return model


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить модель")
def admin_delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    try:
        delete_model(db, model_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
