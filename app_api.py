"""
Точка входа FastAPI-приложения.
Запуск: uvicorn app_api:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from database import engine, Base
from routers import auth, users, balance, predict, history

# Создание таблиц при старте (если ещё не существуют)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ML Service REST API",
    description="REST API для ML-сервиса предсказаний",
    version="1.0.0",
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(balance.router)
app.include_router(predict.router)
app.include_router(history.router)


@app.get("/", tags=["Root"])
def root():
    """Проверка работоспособности сервиса"""
    return {
        "message": "ML Service API работает",
        "docs": "/docs",
    }
