"""
Telegram-бот к ML-сервису.
Команды:
  /start                              — справка
  /register <email> <пароль>          — регистрация
  /login    <email> <пароль>          — авторизация
  /balance                            — текущий баланс
  /deposit  <сумма>                   — пополнить баланс
  /predict  <model_id> <f1> <f2> ...  — предсказание
  /history                            — история ML-запросов
"""

import os
import logging
from typing import Optional, Any, Tuple, Dict

import aiohttp
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://app:8000")

if not BOT_TOKEN:
    raise ValueError("Не задана переменная BOT_TOKEN в .env")

user_tokens: Dict[int, str] = {}
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

async def api_request(
    method: str,
    path: str,
    token: Optional[str] = None,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
) -> Tuple[int, Any]:
    """
    Универсальный HTTP-запрос к REST API.
    Возвращает (status_code, parsed_json).
    """
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{API_BASE_URL}{path}"

    async with aiohttp.ClientSession() as session:
        if method == "GET":
            async with session.get(url, headers=headers) as resp:
                return resp.status, await resp.json()
        elif method == "POST":
            if data:  # form-data (для OAuth2 логина)
                async with session.post(url, headers=headers, data=data) as resp:
                    return resp.status, await resp.json()
            else:  #json
                async with session.post(url, headers=headers, json=json) as resp:
                    return resp.status, await resp.json()
    return 500, {"detail": "Неподдерживаемый HTTP-метод"}


def get_token(telegram_id: int) -> Optional[str]:
    """Получить сохранённый JWT-токен пользователя"""
    return user_tokens.get(telegram_id)


def require_auth_message() -> str:
    return "!!! Вы не авторизованы.\nИспользуйте: /login <email> <пароль>"

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствие и список команд"""
    await message.answer(
        "👋 Привет! Я бот ML-сервиса предсказаний.\n"
        "\n"
        "📌 <b>Доступные команды:</b>\n"
        "\n"
        "🔐 <b>Аутентификация</b>\n"
        "  /register &lt;email&gt; &lt;пароль&gt;\n"
        "  /login &lt;email&gt; &lt;пароль&gt;\n"
        "\n"
        "💰 <b>Баланс</b>\n"
        "  /balance — текущий баланс\n"
        "  /deposit &lt;сумма&gt; — пополнить\n"
        "\n"
        "🤖 <b>ML-предсказания</b>\n"
        "  /predict &lt;model_id&gt; &lt;f1&gt; &lt;f2&gt; ...\n"
        "\n"
        "📋 <b>История</b>\n"
        "  /history — история ML-запросов",
        parse_mode="HTML",
    )

@router.message(Command("register"))
async def cmd_register(message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(
            "Использование:\n/register <email> <пароль>\n\n"
            "Пароль — минимум 8 символов."
        )
        return

    _, email, password = parts
    status_code, body = await api_request(
        "POST",
        "/auth/register",
        json={"email": email, "password": password},
    )

    if status_code == 201:
        await message.answer(
            f"Регистрация успешна!\n"
            f"Email: {body['email']}\n"
            f"Роль: {body['role']}\n\n"
            f"Теперь авторизуйтесь: /login {email} <пароль>"
        )
    else:
        detail = body.get("detail", "Неизвестная ошибка")
        await message.answer(f"❌ Ошибка регистрации:\n{detail}")

@router.message(Command("login"))
async def cmd_login(message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование:\n/login <email> <пароль>")
        return

    _, email, password = parts
    status_code, body = await api_request(
        "POST",
        "/auth/login",
        data={"username": email, "password": password},
    )

    if status_code == 200:
        user_tokens[message.from_user.id] = body["access_token"]
        await message.answer(
            "Авторизация успешна! Токен сохранён.\n\n"
            "Теперь доступны команды:\n"
            "/balance • /deposit • /predict • /history"
        )
    else:
        detail = body.get("detail", "Неизвестная ошибка")
        await message.answer(f"❌ Ошибка входа:\n{detail}")

@router.message(Command("balance"))
async def cmd_balance(message: Message) -> None:
    token = get_token(message.from_user.id)
    if not token:
        await message.answer(require_auth_message())
        return

    status_code, body = await api_request("GET", "/balance/", token=token)

    if status_code == 200:
        await message.answer(f"💰 Ваш баланс: <b>{body['balance']}</b>", parse_mode="HTML")
    elif status_code == 401:
        await message.answer("⚠️ Токен истёк. Повторите /login")
    else:
        await message.answer(f"❌ Ошибка: {body.get('detail', 'Неизвестная ошибка')}")

@router.message(Command("deposit"))
async def cmd_deposit(message: Message) -> None:
    token = get_token(message.from_user.id)
    if not token:
        await message.answer(require_auth_message())
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование:\n/deposit <сумма>")
        return

    try:
        amount = float(parts[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Сумма должна быть положительным числом")
        return

    status_code, body = await api_request(
        "POST",
        "/balance/deposit",
        token=token,
        json={"amount": amount},
    )

    if status_code == 200:
        await message.answer(
            f"✅ Баланс пополнен!\n"
            f"💰 Текущий баланс: <b>{body['balance']}</b>",
            parse_mode="HTML",
        )
    elif status_code == 401:
        await message.answer("⚠️ Токен истёк. Повторите /login")
    else:
        await message.answer(f"❌ Ошибка: {body.get('detail', 'Неизвестная ошибка')}")

@router.message(Command("predict"))
async def cmd_predict(message: Message) -> None:
    token = get_token(message.from_user.id)
    if not token:
        await message.answer(require_auth_message())
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "Использование:\n/predict <model_id> <feat1> <feat2> ...\n\n"
            "Пример:\n/predict 1 3 -1 2"
        )
        return

    try:
        model_id = int(parts[1])
        features = [float(x) for x in parts[2:]]
    except ValueError:
        await message.answer(
            "❌ model_id — целое число, признаки — числа через пробел"
        )
        return
    status_code, body = await api_request(
        "POST",
        "/predict/",
        token=token,
        json={"model_id": model_id, "features": features},
    )

    if status_code == 200:
        await message.answer(
            f"✅ <b>Предсказание выполнено!</b>\n\n"
            f"🆔 Task ID: {body['task_id']}\n"
            f"📊 Статус: {body['status']}\n"
            f"🎯 Результат: {body['output_data']}\n"
            f"💸 Списано: {body['cost']}",
            parse_mode="HTML",
        )
    elif status_code == 402:
        await message.answer(f"💸 Недостаточно средств!\n{body.get('detail', '')}")
    elif status_code == 404:
        await message.answer(f"❌ Модель не найдена: {body.get('detail', '')}")
    elif status_code == 401:
        await message.answer("⚠️ Токен истёк. Повторите /login")
    else:
        await message.answer(f"❌ Ошибка: {body.get('detail', 'Неизвестная ошибка')}")

@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    token = get_token(message.from_user.id)
    if not token:
        await message.answer(require_auth_message())
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование:\n/status <task_uuid>")
        return
    task_uuid = parts[1]
    status_code, body = await api_request("GET", f"/predict/{task_uuid}", token=token)
    if status_code == 200:
        status_emoji = {"pending": "⏳", "completed": "✅", "failed": "❌"}.get(body["status"], "❓")
        text = (
            f"{status_emoji} <b>Статус: {body['status']}</b>\n\n"
            f"🆔 task_id: <code>{body['task_id']}</code>\n"
            f"📥 Вход: {body['input_data']}\n"
        )
        if body.get("output_data"):
            text += f"🎯 Результат: {body['output_data']}\n"
        text += f"📅 Создана: {body['created_at']}"
        await message.answer(text, parse_mode="HTML")
    elif status_code == 404:
        await message.answer("❌ Задача не найдена")
    else:
        await message.answer(f"❌ Ошибка: {body.get('detail', 'Неизвестная ошибка')}")

# ── История ──────────────────────────────────────────────

@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    token = get_token(message.from_user.id)
    if not token:
        await message.answer(require_auth_message())
        return

    status_code, body = await api_request(
        "GET", "/history/tasks", token=token
    )

    if status_code == 200:
        if not body:
            await message.answer("📋 История пуста — вы ещё не делали предсказаний.")
            return

        lines = ["📋 <b>История ML-запросов:</b>\n"]
        for i, task in enumerate(body, start=1):
            status_emoji = "✅" if task["status"] == "completed" else "❌"
            lines.append(
                f"{i}. {status_emoji} <b>[{task['status']}]</b>\n"
                f"   Вход: {task['input_data']}\n"
                f"   Выход: {task['output_data']}\n"
                f"   Дата: {task['created_at']}\n"
            )
        await message.answer("\n".join(lines), parse_mode="HTML")
    elif status_code == 401:
        await message.answer("⚠️ Токен истёк. Повторите /login")
    else:
        await message.answer(f"❌ Ошибка: {body.get('detail', 'Неизвестная ошибка')}")


# ══════════════════════════════════════════════════════════
#  Запуск
# ══════════════════════════════════════════════════════════

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.info("Бот запущен, ожидаю сообщения...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())