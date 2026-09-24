import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers import start, games, stats, ai_analysis, favorites, accuracy
from bot.services.cache_warmer import run_scheduler
from bot.services.notifier import run_scheduler as run_notify_scheduler
from bot.services.prediction_tracker import run_scheduler as run_prediction_scheduler

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set (check your .env / Railway variables)")

    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(games.router)
    dp.include_router(stats.router)
    dp.include_router(ai_analysis.router)
    dp.include_router(favorites.router)
    dp.include_router(accuracy.router)

    await bot.delete_webhook(drop_pending_updates=True)

    warm_task = asyncio.create_task(run_scheduler())
    notify_task = asyncio.create_task(run_notify_scheduler(bot))
    prediction_task = asyncio.create_task(run_prediction_scheduler())
    try:
        await dp.start_polling(bot)
    finally:
        warm_task.cancel()
        notify_task.cancel()
        prediction_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
