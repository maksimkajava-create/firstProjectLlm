# firstProjectLlm

ML-сервис с REST API и Telegram-ботом. Пользователи регистрируются, пополняют баланс и отправляют ML-задачи через бота или Swagger UI. Задачи обрабатываются воркерами через очередь RabbitMQ.

## Стек технологий

- **FastAPI** — REST API
- **aiogram 3** — Telegram-бот
- **PostgreSQL 15** — база данных
- **RabbitMQ** — очередь задач (publisher → workers)
- **nginx** — обратный прокси
- **Docker Compose** — оркестрация

## Структура проекта

```
/
├── app/                    # Основное приложение
│   ├── database/           # Подключение к БД
│   ├── models/             # SQLAlchemy модели
│   ├── routes/             # FastAPI роутеры
│   ├── services/           # crud/ (user, ml_task) + rm/ (RabbitMQ)
│   ├── api.py              # FastAPI приложение
│   ├── main.py             # Запуск API + бота
│   ├── bot.py              # Telegram-бот
│   ├── auth_utils.py       # JWT аутентификация
│   ├── schemas.py          # Pydantic схемы
│   ├── requirements.txt
│   └── Dockerfile
├── ml_worker/              # ML-воркеры (2 реплики)
│   ├── worker.py
│   └── Dockerfile
├── nginx/                  # Обратный прокси
│   ├── nginx.conf
│   └── Dockerfile
├── .env
└── docker-compose.yml
```

## Быстрый старт

### 1. Создай `.env` в корне проекта

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=твой_пароль
POSTGRES_DB=mlservice
DATABASE_URL=postgresql://admin:твой_пароль@database:5432/mlservice
SECRET_KEY=секретный_ключ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
BOT_TOKEN=токен_от_botfather
API_BASE_URL=http://app:8000
LLM_API_KEY=ollama
LLM_BASE_URL=http://ollama:11434/v1
LLM_MODEL_ID=2          
LLM_POLL_TIMEOUT=120    
```

> Токен бота получи у [@BotFather](https://t.me/BotFather)

### 2. Запусти

```bash
docker compose up --build
```

### 3. Swagger UI

```
http://localhost/docs
```

## Сервисы

| Сервис      | Адрес                  |
|-------------|------------------------|
| Swagger UI  | http://localhost/docs  |
| RabbitMQ UI | http://localhost:15672 |
| PostgreSQL  | localhost:5432         |

## Архитектура обработки ML-задач

```
POST /predict → publisher → очередь RabbitMQ → worker-1 
                                                          БД (результат)
                                             → worker-2 
GET /predict/{task_uuid} → статус задачи
```

## Команды Telegram-бота

| Команда                          | Описание                       |
|----------------------------------|--------------------------------|
| `/start`                         | Справка                        |
| `/register <email> <пароль>`     | Регистрация                    |
| `/login <email> <пароль>`        | Авторизация                    |
| `/balance`                       | Текущий баланс                 |
| `/deposit <сумма>`               | Пополнить баланс               |
| `/predict <model_id> <f1> <f2>`  | ML-предсказание                |
|`/prompt   <текст>`               |запрос к LLM (Ollama)           |
|`/prompt   <model_id> <текст>`    | запрос к конкретной LLM-модели |
| `/history`                       | История запросов               |
