"""
Точка входа: запускает FastAPI (uvicorn) и Telegram-бота параллельно.
"""
import asyncio
import logging

import uvicorn

from bot import dp, bot


async def run_api() -> None:
    config = uvicorn.Config(
        "api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_bot() -> None:
    logging.info("Бот запущен, ожидаю сообщения...")
    await dp.start_polling(bot)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    await asyncio.gather(run_api(), run_bot())


if __name__ == "__main__":
    asyncio.run(main())
