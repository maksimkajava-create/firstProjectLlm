"""
Telegram-бот к ML-сервису.
Команды:
  /start                              — справка
  /register <email> <пароль>          — регистрация
  /login    <email> <пароль>          — авторизация
  /balance                            — текущий баланс
  /deposit  <сумма>                   — пополнить баланс
  /predict  <model_id> <f1> <f2> ...  — предсказание (числовые признаки)
  /prompt   <текст>                   — запрос к LLM (Ollama)
  /prompt   <model_id> <текст>        — запрос к конкретной LLM-модели
  /status   <task_uuid>               — статус задачи
  /history                            — история ML-запросов
"""

import os
import asyncio
import logging
from typing import Optional, Any, Tuple, Dict

import aiohttp
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://app:8000")
LLM_MODEL_ID: int = int(os.getenv("LLM_MODEL_ID", "1"))
LLM_POLL_TIMEOUT: int = int(os.getenv("LLM_POLL_TIMEOUT", "120"))

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
            if data:
                async with session.post(url, headers=headers, data=data) as resp:
                    return resp.status, await resp.json()
            else:
                async with session.post(url, headers=headers, json=json) as resp:
                    return resp.status, await resp.json()
    return 500, {"detail": "Неподдерживаемый HTTP-метод"}


async def poll_task_result(
    task_uuid: str,
    token: str,
    timeout: int = LLM_POLL_TIMEOUT,
    interval: float = 2.0,
) -> Tuple[int, Any]:
    """
    Опрашивает GET /predict/{task_uuid} пока статус не станет
    completed/failed или не истечёт таймаут.
    """
    elapsed = 0.0
    while elapsed < timeout:
        status_code, body = await api_request(
            "GET", f"/predict/{task_uuid}", token=token
        )
        if status_code != 200:
            return status_code, body

        task_status = body.get("status", "")
        if task_status in ("completed", "failed"):
            return status_code, body

        await asyncio.sleep(interval)
        elapsed += interval

    return status_code, body


def get_token(telegram_id: int) -> Optional[str]:
    return user_tokens.get(telegram_id)


def require_auth_message() -> str:
    return "!!! Вы не авторизованы.\nИспользуйте: /login <email> <пароль>"

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
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
        "💬 <b>LLM-запросы (Ollama)</b>\n"
        "  /prompt &lt;ваш вопрос&gt;\n"
        "  /prompt &lt;model_id&gt; &lt;ваш вопрос&gt;\n"
        "  ...или просто напишите текст без команды\n"
        "\n"
        "📋 <b>Прочее</b>\n"
        "  /status &lt;task_uuid&gt; — статус задачи\n"
        "  /history — история запросов",
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
            "/balance • /deposit • /predict • /prompt • /history"
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
            f"✅ <b>Задача создана!</b>\n\n"
            f"🆔 Task ID: <code>{body['task_id']}</code>\n"
            f"📊 Статус: {body['status']}\n"
            f"💸 Списано: {body['cost']}\n\n"
            f"Проверить результат: /status {body['task_id']}",
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

async def _handle_prompt(message: Message, prompt_text: str, model_id: int = LLM_MODEL_ID) -> None:
    """
    Отправляет промт через POST /predict/ и ждёт результат
    """
    token = get_token(message.from_user.id)
    if not token:
        await message.answer(require_auth_message())
        return

    if not prompt_text.strip():
        await message.answer("❌ Промт не может быть пустым")
        return

    thinking_msg = await message.answer("🤔 Отправляю запрос...")

    status_code, body = await api_request(
        "POST",
        "/predict/",                    # тот же эндпоинт, что и для predict
        token=token,
        json={
            "model_id": model_id,       # id Ollama-модели в БД
            "prompt": prompt_text,       # текст промта
        },
    )

    if status_code != 200:
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        if status_code == 402:
            await message.answer(f"💸 Недостаточно средств!\n{body.get('detail', '')}")
        elif status_code == 404:
            await message.answer(f"❌ Модель не найдена (model_id={model_id}): {body.get('detail', '')}")
        elif status_code == 401:
            await message.answer("⚠️ Токен истёк. Повторите /login")
        else:
            await message.answer(f"❌ Ошибка: {body.get('detail', 'Неизвестная ошибка')}")
        return

    task_id = body.get("task_id")
    cost = body.get("cost", "—")

    try:
        await thinking_msg.edit_text(
            f"⏳ Задача создана, жду ответ от LLM...\n"
            f"🆔 Task: <code>{task_id}</code>\n"
            f"💸 Списано: {cost}",
            parse_mode="HTML",
        )
    except Exception:
        pass

    status_code, result = await poll_task_result(task_id, token)

    try:
        await thinking_msg.delete()
    except Exception:
        pass

    if status_code != 200:
        await message.answer(f"❌ Ошибка при проверке статуса: {result.get('detail', '')}")
        return

    task_status = result.get("status", "unknown")

    if task_status == "completed":
        output = result.get("output_data", "Нет данных")

        answer = (
            f"💬 <b>Ответ LLM:</b>\n\n"
            f"{output['response']}\n\n"
            f"───────────\n"
            f"🆔 Task: <code>{task_id}</code>\n"
            f"💸 Списано: {cost}"
        )
        # Telegram: макс 4096 символов на сообщение
        if len(answer) > 4096:
            for i in range(0, len(answer), 4096):
                chunk = answer[i:i + 4096]
                await message.answer(chunk, parse_mode="HTML")
        else:
            await message.answer(answer, parse_mode="HTML")

    elif task_status == "failed":
        await message.answer(
            f"❌ <b>Ошибка обработки</b>\n\n"
            f"🆔 Task: <code>{task_id}</code>\n"
            f"📄 {result.get('output_data', 'Нет деталей')}",
            parse_mode="HTML",
        )
    else:
        # pending — таймаут
        await message.answer(
            f"⏳ <b>LLM ещё думает...</b>\n\n"
            f"Задача не завершилась за {LLM_POLL_TIMEOUT} сек.\n"
            f"Проверьте позже:\n"
            f"/status {task_id}",
            parse_mode="HTML",
        )


@router.message(Command("prompt"))
async def cmd_prompt(message: Message) -> None:
    """
    /prompt <текст>                — промт к LLM (model_id по умолчанию)
    /prompt <model_id> <текст>     — промт к конкретной модели
    """
    raw = message.text.removeprefix("/prompt").strip()

    if not raw:
        await message.answer(
            "Использование:\n"
            "/prompt &lt;ваш вопрос&gt;\n"
            "/prompt &lt;model_id&gt; &lt;ваш вопрос&gt;\n\n"
            "Примеры:\n"
            "/prompt Что такое нейронная сеть?\n"
            "/prompt 2 Напиши функцию на Python",
            parse_mode="HTML",
        )
        return

    parts = raw.split(maxsplit=1)
    try:
        model_id = int(parts[0])
        prompt_text = parts[1] if len(parts) > 1 else ""
    except ValueError:
        model_id = LLM_MODEL_ID
        prompt_text = raw

    if not prompt_text.strip():
        await message.answer("❌ Промт не может быть пустым")
        return

    await _handle_prompt(message, prompt_text, model_id)

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
            await message.answer("📋 История пуста — вы ещё не делали запросов.")
            return

        lines = ["📋 <b>История запросов:</b>\n"]
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

@router.message()
async def handle_free_text(message: Message) -> None:
    """Любое сообщение без команды == промт к LLM"""
    if not message.text:
        await message.answer("❌ Я понимаю только текстовые сообщения")
        return

    await _handle_prompt(message, message.text)


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