"""
Точка входа FastAPI-приложения.
Запуск: uvicorn api:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from database.connection import Base, engine
from routes import auth, users, balance, predict, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
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
