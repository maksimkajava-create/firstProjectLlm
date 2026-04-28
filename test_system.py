"""
Тесты всех обязательных сценариев
1) Поднимаем всю систему
    docker-compose up -d
2) Инициализируем БД 
    docker-compose exec app python init_db.py
3) Ставим зависимости для тестов
    pip install -r requirements-test.txt
4) Запускаем тесты
    pytest test_system.py -v -s
"""

import time
import uuid
import pytest
import requests


BASE_URL = "http://localhost/api"

POLL_TIMEOUT = 30
POLL_INTERVAL = 2

def unique_email():
    """Генерирует уникальный email для каждого теста"""
    return f"test_{uuid.uuid4().hex[:8]}@test.com"

def register_user(email: str, password: str) -> requests.Response:
    """POST /auth/register - JSON"""
    return requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password},
    )

def login_user(email: str, password: str) -> requests.Response:
    """POST /auth/login - form-data (OAuth2PasswordRequestForm)"""
    return requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": email, "password": password},
    )

def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

def poll_task(task_uuid: str, token: str, timeout=POLL_TIMEOUT) -> dict:
    """Опрашивает GET /predict/{uuid} пока не completed/faild"""
    elapsed = 0
    while elapsed < timeout:
        resp = requests.get(
            f"{BASE_URL}/predict/{task_uuid}",
            headers=auth_headers(token),
        )
        if resp.status_code == 200:
            body = resp.json()
            if body["status"] in ("completed", "failed"):
                return body
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    return resp.json() if resp.status_code == 200 else {"status": "timeout"}

@pytest.fixture(scope="module")
def test_user():
    """Создаёт пользователя, логинится, возвращает данные"""
    email = unique_email()
    password = "TestPass123"

    resp = register_user(email, password)
    assert resp.status_code == 201, f"Регистрация: {resp.text}"

    resp = login_user(email, password)
    assert resp.status_code == 200, f"Логин: {resp.text}"
    token = resp.json()["access_token"]

    return {
        "email": email,
        "password": password,
        "token": token,
        "headers": auth_headers(token),
    }

class TestEnvironment:
    """Проверка системы"""

    def test_api_root_responds(self):
        """GET\ - корневой эндпоинт FastAPI"""
        resp = requests.get(f"{BASE_URL}/")
        assert resp.status_code == 200
        assert "ML Service" in resp.json().get("message", "")

    def test_docs_available(self):
        """Swagger доступен"""
        resp = requests.get(f"{BASE_URL}/docs")
        assert resp.status_code == 200

class TestUsers:
    """Тесты пользователя"""
    def test_register_new_user(self):
        """Создание нового пользователя"""
        email = unique_email()
        resp = register_user(email, "StrongPass1")
        assert resp.status_code == 201

        body = resp.json()
        assert body["email"] == email
        assert body["role"] == "client"

    def test_register_duplicate_email(self):
        """Повторная регистрация с тем же email: 409"""
        email = unique_email()
        register_user(email, "StrongPass1")

        resp = register_user(email, "StrongPass1")
        assert resp.status_code == 409

    def test_register_short_password(self):
        """Пароль короче 8 символов: 422"""
        resp = register_user(unique_email(), "short")
        assert resp.status_code == 422

    def test_register_invalid_email(self):
        """Некорректный формат email: 422"""
        resp = register_user("not-an-email", "StrongPass1")
        assert resp.status_code == 422

    def test_login_success(self):
        """Авторизация с верными данными"""
        email = unique_email()
        register_user(email, "StrongPass1")

        resp = login_user(email, "StrongPass1")
        assert resp.status_code == 200

        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Авторизация с неверным паролем: 401"""
        email = unique_email()
        register_user(email, "StrongPass1")

        resp = login_user(email, "WrongPassword")
        assert resp.status_code == 401

    def test_login_nonexistent_user(self):
        """Авторизация несуществующего пользователя: 401"""
        resp = login_user("nobody@nowhere.com", "whatever1")
        assert resp.status_code == 401

    def test_reauth_returns_valid_token(self):
        """Повторная авторизация - оба токена рабочие"""
        email = unique_email()
        register_user(email, "StrongPass1")

        resp1 = login_user(email, "StrongPass1")
        resp2 = login_user(email, "StrongPass1")
        assert resp1.status_code == 200
        assert resp2.status_code == 200

        #Оба токена валидны - можно получить профиль
        for resp in (resp1, resp2):
            token = resp.json()["access_token"]
            me = requests.get(
                f"{BASE_URL}/users/me",
                headers=auth_headers(token),
            )
            assert me.status_code == 200
            assert me.json()["email"] == email

    def test_access_without_token(self):
        """Запрос без токена: 401/403"""
        resp = requests.get(f"{BASE_URL}/users/me")
        assert resp.status_code in (401, 403)

class TestBalance:
    """Тесты баланса"""
    def test_initial_balance_is_zero(self, test_user):
        """Новый пользователь - баланс 0"""
        resp = requests.get(
            f"{BASE_URL}/balance/",
            headers=test_user["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["balance"] == 0.0

    def test_deposit(self, test_user):
        """Пополнение баланса на 100"""
        resp = requests.post(
            f"{BASE_URL}/balance/deposit",
            json={"amount": 100.0},
            headers=test_user["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["balance"] == 100.0

    def test_deposit_updates_balance_correctly(self, test_user):
        """Повторное пополнение - баланс суммируется"""
        #Баланс до
        resp = requests.get(f"{BASE_URL}/balance/", headers=test_user["headers"])
        before = resp.json()["balance"]

        #Пополняем на 50
        resp = requests.post(
            f"{BASE_URL}/balance/deposit",
            json={"amount": 50.0},
            headers=test_user["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["balance"] == before + 50.0

        #Проверяем через отдельный GET
        resp = requests.get(f"{BASE_URL}/balance/", headers=test_user["headers"])
        assert resp.json()["balance"] == before + 50.0

    def test_deposit_negative_amount(self, test_user):
        """Пополнение на отрицательную сумму: 422"""
        resp = requests.post(
            f"{BASE_URL}/balance/deposit",
            json={"amount": -10.0},
            headers=test_user["headers"],
        )
        assert resp.status_code == 422

    def test_deposit_zero_amount(self, test_user):
        """Пополнение на 0: 422"""
        resp = requests.post(
            f"{BASE_URL}/balance/deposit",
            json={"amount": 0},
            headers=test_user["headers"],
        )
        assert resp.status_code == 422

    def test_balance_without_auth(self):
        """Баланс без авторизации: 401/403"""
        resp = requests.get(f"{BASE_URL}/balance/")
        assert resp.status_code in (401, 403)

class TestMLPredict:
    """Тесты предсказаний"""
    def test_predict_success_and_deduction(self, test_user):
        """
        Успешный ML-запрос:
        1. Пополняем баланс
        2. Запоминаем баланс
        3. Отправляем predict
        4. Проверяем списание
        5. Проверяем результат через polling
        """
        headers = test_user["headers"]

        #Пополняем, чтобы точно хватило
        requests.post(
            f"{BASE_URL}/balance/deposit",
            json={"amount": 200.0},
            headers=headers,
        )

        #Баланс ДО
        resp = requests.get(f"{BASE_URL}/balance/", headers=headers)
        balance_before = resp.json()["balance"]

        #Отправляем предсказание (SimpleClassifier, model_id=1, cost=15)
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1, "features": [1.0, 2.0, -3.0]},
            headers=headers,
        )
        assert resp.status_code == 200, f"Predict failed: {resp.text}"

        body = resp.json()
        assert "task_id" in body
        assert body["status"] == "pending"
        assert body["cost"] == 15.0
        task_uuid = body["task_id"]

        #Баланс после- кредиты списались сразу
        resp = requests.get(f"{BASE_URL}/balance/", headers=headers)
        balance_after = resp.json()["balance"]
        assert balance_after == balance_before - 15.0, (
            f"Списание: было {balance_before}, стало {balance_after}, "
            f"ожидалось {balance_before - 15.0}"
        )

        #Ждём результат от воркера
        result = poll_task(task_uuid, test_user["token"])
        assert result["status"] == "completed", f"Task: {result}"
        assert result["output_data"] is not None

    def test_predict_insufficient_balance(self):
        """Predict при нулевом балансе: 402"""
        #Новый пользователь с балансом 0
        email = unique_email()
        register_user(email, "TestPass12")
        resp = login_user(email, "TestPass12")
        token = resp.json()["access_token"]

        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1, "features": [1.0, 2.0]},
            headers=auth_headers(token),
        )
        assert resp.status_code == 402

    def test_predict_no_deduction_on_insufficient(self):
        """При отказе (402) баланс не меняется"""
        email = unique_email()
        register_user(email, "TestPass12")
        resp = login_user(email, "TestPass12")
        token = resp.json()["access_token"]
        headers = auth_headers(token)

        #Пополняем на 5 (SimpleClassifier стоит 15)
        requests.post(
            f"{BASE_URL}/balance/deposit",
            json={"amount": 5.0},
            headers=headers,
        )

        #Баланс до
        resp = requests.get(f"{BASE_URL}/balance/", headers=headers)
        balance_before = resp.json()["balance"]

        #Запрос - должен быть 402
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1, "features": [1.0]},
            headers=headers,
        )
        assert resp.status_code == 402

        #Баланс после - не изменился
        resp = requests.get(f"{BASE_URL}/balance/", headers=headers)
        assert resp.json()["balance"] == balance_before

    def test_predict_nonexistent_model(self, test_user):
        """Несуществующая модель: 404"""
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 9999, "features": [1.0]},
            headers=test_user["headers"],
        )
        assert resp.status_code == 404

    def test_predict_invalid_input_no_features_no_prompt(self, test_user):
        """Нет ни features, ни prompt: 422"""
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1},
            headers=test_user["headers"],
        )
        assert resp.status_code == 422

    def test_predict_empty_body(self, test_user):
        """Пустое тело запроса: 422"""
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={},
            headers=test_user["headers"],
        )
        assert resp.status_code == 422

    def test_predict_without_auth(self):
        """Predict без токена: 401/403"""
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1, "features": [1.0]},
        )
        assert resp.status_code in (401, 403)

    def test_get_task_status(self, test_user):
        """GET /predict/{uuid} - получение статуса задачи"""
        headers = test_user["headers"]

        #Пополняем и делаем запрос
        requests.post(f"{BASE_URL}/balance/deposit", json={"amount": 100}, headers=headers)
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1, "features": [5.0, -1.0]},
            headers=headers,
        )
        task_uuid = resp.json()["task_id"]

        #Проверяем статус
        resp = requests.get(
            f"{BASE_URL}/predict/{task_uuid}",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["task_id"] == task_uuid
        assert body["status"] in ("pending", "completed", "failed")
        assert "input_data" in body

    def test_get_nonexistent_task(self, test_user):
        """Несуществующая задача: 404"""
        resp = requests.get(
            f"{BASE_URL}/predict/nonexistent-uuid-12345",
            headers=test_user["headers"],
        )
        assert resp.status_code == 404

    def test_predict_with_prompt(self, test_user):
        """Predict с промтом (LLM-модель, model_id=2)"""
        headers = test_user["headers"]

        requests.post(f"{BASE_URL}/balance/deposit", json={"amount": 100}, headers=headers)

        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 2, "prompt": "Скажи привет"},
            headers=headers,
        )
        # Может быть 200, если Ollama доступна, или 503, если нет
        if resp.status_code == 200:
            body = resp.json()
            assert "task_id" in body
            #Ждём результат
            result = poll_task(body["task_id"], test_user["token"], timeout=60)
            assert result["status"] in ("completed", "failed")
        else:
            #Ollama может быть недоступна - это допустимо
            assert resp.status_code in (503, 500)

class TestHistory:
    """Тесты истории"""
    def test_task_history_not_empty(self, test_user):
        """После predict-запросов история задач не пуста"""
        resp = requests.get(
            f"{BASE_URL}/history/tasks",
            headers=test_user["headers"],
        )
        assert resp.status_code == 200
        tasks = resp.json()
        assert isinstance(tasks, list)
        assert len(tasks) > 0, "История задач пуста после выполненных запросов"

    def test_task_history_has_correct_fields(self, test_user):
        """Каждая запись истории содержит нужные поля"""
        resp = requests.get(
            f"{BASE_URL}/history/tasks",
            headers=test_user["headers"],
        )
        task = resp.json()[0]
        assert "id" in task
        assert "model_id" in task
        assert "input_data" in task
        assert "status" in task
        assert "created_at" in task

    def test_transaction_history_not_empty(self, test_user):
        """После депозитов и predict история транзакций не пуста"""
        resp = requests.get(
            f"{BASE_URL}/history/transactions",
            headers=test_user["headers"],
        )
        assert resp.status_code == 200
        txns = resp.json()
        assert isinstance(txns, list)
        assert len(txns) > 0, "История транзакций пуста"

    def test_transaction_history_has_deposits_and_debits(self, test_user):
        """История содержит и пополнения (credit), и списания (debit)"""
        resp = requests.get(
            f"{BASE_URL}/history/transactions",
            headers=test_user["headers"],
        )
        txns = resp.json()
        types = {t["transaction_type"] for t in txns}
        assert "credit" in types, f"Нет пополнений. Типы: {types}"
        assert "debit" in types, f"Нет списаний. Типы: {types}"

    def test_transaction_matches_actions(self, test_user):
        """
        Сквозная проверка:
        Делаем deposit, predict: проверяем, что в истории появились соответствующие записи.
        """
        headers = test_user["headers"]

        #Запоминаем кол-во транзакций ДО
        resp = requests.get(f"{BASE_URL}/history/transactions", headers=headers)
        txns_before = len(resp.json())

        resp = requests.get(f"{BASE_URL}/history/tasks", headers=headers)
        tasks_before = len(resp.json())

        #Deposit
        requests.post(
            f"{BASE_URL}/balance/deposit",
            json={"amount": 50.0},
            headers=headers,
        )

        #Predict
        requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1, "features": [10.0]},
            headers=headers,
        )

        #Проверяем: +1 credit (deposit) +1 debit (predict) = +2 транзакции
        resp = requests.get(f"{BASE_URL}/history/transactions", headers=headers)
        txns_after = len(resp.json())
        assert txns_after >= txns_before + 2, (
            f"Ожидалось +2 транзакции, было {txns_before}, стало {txns_after}"
        )

        #+1 задача
        resp = requests.get(f"{BASE_URL}/history/tasks", headers=headers)
        tasks_after = len(resp.json())
        assert tasks_after >= tasks_before + 1, (
            f"Ожидалась +1 задача, было {tasks_before}, стало {tasks_after}"
        )

    def test_history_without_auth(self):
        """История без токена: 401/403"""
        resp = requests.get(f"{BASE_URL}/history/tasks")
        assert resp.status_code in (401, 403)

        resp = requests.get(f"{BASE_URL}/history/transactions")
        assert resp.status_code in (401, 403)

    def test_history_is_user_isolated(self):
        """Пользователь видит только свою историю"""
        #Создаём двух пользователей
        email1, email2 = unique_email(), unique_email()
        register_user(email1, "TestPass12")
        register_user(email2, "TestPass12")
        token1 = login_user(email1, "TestPass12").json()["access_token"]
        token2 = login_user(email2, "TestPass12").json()["access_token"]
        h1, h2 = auth_headers(token1), auth_headers(token2)

        #User1 делает deposit + predict
        requests.post(f"{BASE_URL}/balance/deposit", json={"amount": 100}, headers=h1)
        requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1, "features": [1.0]},
            headers=h1,
        )

        #User2 - история пуста
        resp = requests.get(f"{BASE_URL}/history/tasks", headers=h2)
        assert resp.status_code == 200
        assert len(resp.json()) == 0, "User2 видит чужие задачи!"

        resp = requests.get(f"{BASE_URL}/history/transactions", headers=h2)
        assert resp.status_code == 200
        assert len(resp.json()) == 0, "User2 видит чужие транзакции!"

class TestEndToEnd:
    """Сквозное тестирование"""
    def test_full_user_journey(self):
        """
        Полный путь:
        регистрация, логин, баланс=0, deposit 100,
        баланс=100, predict (cost=15), баланс=85, poll 
        результат: история содержит всё
        """
        email = unique_email()
        password = "E2ETestPass1"

        #Регистрация
        resp = register_user(email, password)
        assert resp.status_code == 201
        print(f"Регистрация: {email}")

        #Логин
        resp = login_user(email, password)
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = auth_headers(token)
        print("Логин: токен получен")

        #Начальный баланс = 0
        resp = requests.get(f"{BASE_URL}/balance/", headers=headers)
        assert resp.json()["balance"] == 0.0
        print("Начальный баланс: 0.0")

        #Deposit 100
        resp = requests.post(
            f"{BASE_URL}/balance/deposit",
            json={"amount": 100.0},
            headers=headers,
        )
        assert resp.json()["balance"] == 100.0
        print("Депозит: баланс = 100.0")

        #Predict (SimpleClassifier, cost=15)
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json={"model_id": 1, "features": [3.0, -1.0, 2.0]},
            headers=headers,
        )
        assert resp.status_code == 200
        task_uuid = resp.json()["task_id"]
        print(f"Predict: task_id={task_uuid}")

        #Баланс = 85
        resp = requests.get(f"{BASE_URL}/balance/", headers=headers)
        assert resp.json()["balance"] == 85.0
        print("Баланс после predict: 85.0")

        #Результат
        result = poll_task(task_uuid, token)
        assert result["status"] == "completed"
        assert result["output_data"] is not None
        print(f"Результат: {result['output_data']}")

        #История задач
        resp = requests.get(f"{BASE_URL}/history/tasks", headers=headers)
        tasks = resp.json()
        assert len(tasks) == 1
        assert tasks[0]["status"] == "completed"
        print("История задач: 1 запись")

        #история транзакций
        resp = requests.get(f"{BASE_URL}/history/transactions", headers=headers)
        txns = resp.json()
        assert len(txns) == 2  #1 credit (deposit) + 1 debit (predict)
        types = {t["transaction_type"] for t in txns}
        assert types == {"credit", "debit"}
        print("История транзакций: 2 записи (credit + debit)")
        print("СКвозной тест пройден!")
