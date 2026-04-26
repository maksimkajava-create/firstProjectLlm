from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="client")

    # Связи
    transactions = relationship("Transaction", back_populates="user")
    tasks = relationship("MLTask", back_populates="user")
    account = relationship("Account", back_populates="user", uselist=False)


class Account(Base):
    """Счёт пользователя — отвечает только за баланс"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Float, default=0.0)

    # Связь
    user = relationship("User", back_populates="account")


class MLModelConfig(Base):
    """Описание ML-модели, доступной в системе"""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    cost_per_prediction = Column(Float, nullable=False)
    model_type = Column(String, default="classifier")
    tasks = relationship("MLTask", back_populates="model")


class MLTask(Base):
    """История запросов и предсказаний"""
    __tablename__ = "ml_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_uuid = Column(String, unique=True, index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)

    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tasks")
    model = relationship("MLModelConfig", back_populates="tasks")
    transaction = relationship("Transaction", back_populates="task", uselist=False)


class Transaction(Base):
    """История финансовых операций"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("ml_tasks.id"), nullable=True)

    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    task = relationship("MLTask", back_populates="transaction")

