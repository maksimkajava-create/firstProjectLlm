"""
Объектная модель сервиса 
Запуск: python main.py
"""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from typing import Any, Dict, List, Optional
import uuid
import random

import re


def give_next_result_id() -> int:
    """Новый уникальный числовой id результата (из UUID, 12 цифр)"""
    return uuid.uuid4().int % (10**12)


def random_demo_input() -> Dict[str, Any]:
    """Случайный список признаков — для вызова из main"""
    feature_values = [random.randint(-5, 5) for _ in range(3)]
    return {"features": feature_values}


@dataclass
class User:
    """
    Класс для представления пользователя в системе ML-сервиса

    Attributes:
        id (int): Уникальный идентификатор пользователя
        email (str): Email (логин)
        password (str): Пароль
        password_hash: Хэш пароля
        role (str): Роль пользователя, например 'client' или 'admin'
    """

    id: int
    email: str
    password: str
    role: str
    password (str): InitVar[str]
    password_hash: str = field(init=False)

def __post_init__(self, password: str) -> None:
        self._validate_email()
        self._validate_and_hash_password(password)

def _validate_email(self) -> None:
        """Проверяет корректность email"""
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if not email_pattern.match(self.email):
            raise ValueError("Некорректный формат email")

def _validate_and_hash_password(self, password: str) -> None:
        """Проверяет минимальную длину пароля и сохраняет только его хэш"""
        if len(password) < 8:
            raise ValueError("Пароль должен быть не короче 8 символов")
        # Создаем хэш пароля с помощью sha256
        self.password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

@dataclass
class Account:
    """
    Класс для управления балансом
    Attributes:
        balance (float): Баланс для оплаты предсказаний
    """
    balance: float = 0.0

    def __post_init__(self) -> None:
        self._validate_balance()


    def _validate_balance(self) -> None:
        """Проверяет начальный баланс"""
        if self.balance < 0:
            raise ValueError("Баланс не может быть отрицательным")

    def deposit(self, amount: float) -> None:
        """Пополняет баланс"""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть больше нуля")
        self.balance = self.balance + amount

    def withdraw(self, amount: float) -> None:
        """Списывает средства"""
        if amount > self.balance:
            raise ValueError("Недостаточно средств на балансе")
        self.balance = self.balance - amount




def make_test_users() -> List[User]:
    """Три тестовых пользователя: при каждом запуске другие email и баланс"""
    users: List[User] = []
    for i in range(1, 4):
        randomBalance = float(random.randint(50, 300))
        suffix = random.randint(1000, 9999)
        user = User(
            id=i,
            email=f"user{i}_{suffix}@mail.ru",
            password="password123",
            role="client",
            account=Account(balance=randomBalance),)
        users.append(user)
    return users


@dataclass
class Transaction:
    """
    Базовый класс финансовой транзакции

    Attributes:
        amount (float): Сумма операции
        created_at (datetime): Дата и время операции
        user (User): Пользователь, к которому относится транзакция
        ml_task (Optional[MLTask]): Связанная задача, если есть
    """

    amount: float
    created_at: datetime
    user: User
    ml_task: Optional["MLTask"] = None

    def apply(self) -> None:
        """Базовый метод; в наследниках выполняет конкретное действие"""
        raise NotImplementedError("Вызов apply у базового Transaction не предусмотрен")


@dataclass
class CreditTransaction(Transaction):
    """Транзакция пополнения баланса (зачисление средств)"""

    def apply(self) -> None:
        """Зачисляет сумму на баланс пользователя"""
        self.user.deposit(self.amount)


@dataclass
class DebitTransaction(Transaction):
    """Транзакция списания (оплата предсказания и т.п.)"""

    def apply(self) -> None:
        """Списывает сумму с баланса пользователя"""
        self.user.withdraw(self.amount)


@dataclass
class MLModel:
    """
    Базовое описание ML-модели в системе

    Attributes:
        id (int): Идентификатор модели
        description (str): Текстовое описание модели
        cost_per_prediction (float): Стоимость одного предсказания
    """

    id: int
    description: str
    cost_per_prediction: float

    def predict(self, input_data: Dict[str, Any]) -> Any:
        """Выполняет предсказание, в наследнике должна быть своя реализация"""
        raise NotImplementedError("Реализуйте predict в классе-наследнике")


@dataclass
class SimpleClassifierModel(MLModel):
    """
    Классификатор по сумме признаков метка A или B

    Если сумма признаков неотрицательная A, иначе B
    """

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Считает сумму признаков и возвращает словарь с полем label"""
        feature_values = input_data.get("features", [])
        features_sum = 0
        for value in feature_values:
            features_sum = features_sum + value
        if features_sum >= 0:
            label = "A"
        else:
            label = "B"
        return {"label": label}


@dataclass
class PredictionResult:
    """
    Результат выполнения предсказания по задаче

    Attributes:
        id (int): Уникальный идентификатор результата
        ml_task (MLTask): Задача, для которой получен результат
        output_data (Any): Данные, вернувшиеся из модели
        created_at (datetime): Время формирования результата
    """

    id: int
    ml_task: "MLTask"
    output_data: Any
    created_at: datetime


@dataclass
class MLTask:
    """
    Задача на выполнение предсказания для выбранной ML-модели

    Attributes:
        id (int): Идентификатор задачи
        input_data (Dict[str, Any]): Входные данные для модели
        status (str): Статус: pending, running, completed или failed
        user (User): Пользователь-заказчик
        model (MLModel): Используемая модель
        result (Optional[PredictionResult]): Результат после успешного выполнения
    """

    id: int
    input_data: Dict[str, Any]
    status: str
    user: User
    model: MLModel
    result: Optional[PredictionResult] = None

    def __post_init__(self) -> None:
        self._validate_status()

    def _validate_status(self) -> None:
        """Проверяет, что статус входит в допустимый набор"""
        allowed_statuses = ["pending", "running", "completed", "failed"]
        if self.status not in allowed_statuses:
            raise ValueError(f"Недопустимый status, ожидается одно из: {allowed_statuses}")

    def start_processing(self, history: "MLRequestHistory") -> PredictionResult:
        """
        Запускает обработку: предсказание, списание стоимости, запись в историю

        Returns:
            PredictionResult: созданный объект результата предсказания
        """
        self.status = "running"
        try:
            prediction_output = self.model.predict(self.input_data)

            debit_transaction = DebitTransaction(
                amount=self.model.cost_per_prediction,
                created_at=datetime.now(),
                user=self.user,
                ml_task=self,
            )
            debit_transaction.apply()

            result_id = give_next_result_id()
            self.result = PredictionResult(
                id=result_id,
                ml_task=self,
                output_data=prediction_output,
                created_at=datetime.now(),
            )
            self.status = "completed"
            history.add_record(self.user, self, self.result)
            return self.result
        except Exception:
            self.status = "failed"
            raise


@dataclass
class HistoryRecord:
    """
    Одна запись в журнале запросов

    Attributes:
        user_id (int): Идентификатор пользователя
        task_id (int): Идентификатор задачи
        result_id (int): Идентификатор результата
        recorded_at (datetime): Время записи в историю
    """

    user_id: int
    task_id: int
    result_id: int
    recorded_at: datetime


@dataclass
class MLRequestHistory:
    """
    История запросов

    Attributes:
        records (List[HistoryRecord]): Список записей истории
    """

    records: List[HistoryRecord] = field(default_factory=list)

    def add_record(self, user: User, ml_task: MLTask, result: PredictionResult) -> None:
        """Добавляет запись о выполненной задаче и результате"""
        history_record = HistoryRecord(
            user_id=user.id,
            task_id=ml_task.id,
            result_id=result.id,
            recorded_at=datetime.now(),
        )
        self.records.append(history_record)


def main() -> None:
    try:
        test_users = make_test_users()
        demo_model = SimpleClassifierModel(
            id=1,
            description="Классификатор по сумме признаков",
            cost_per_prediction=10.0,
        )
        request_history = MLRequestHistory()

        for task_index, demo_user in enumerate(test_users, start=1):
            demo_input = random_demo_input()
            demo_task = MLTask(
                id=task_index,
                input_data=demo_input,
                status="pending",
                user=demo_user,
                model=demo_model,
            )
            prediction_result = demo_task.start_processing(request_history)

            print(f"Пользователь #{task_index}: id={demo_user.id}, email={demo_user.email}")
            print(f"Id результата: {prediction_result.id}")
            print(f"Вход в модель: {demo_input}")
            print(f"Задача: status={demo_task.status}, вывод модели={prediction_result.output_data}")

        print("---")
        print(f"Всего записей в истории: {len(request_history.records)}")
    except ValueError as error:
        print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()
