

















import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, DB_PATH, FETCH_INTERVAL_MINUTES
from database.db import Database
from handlers.user import router
from services.job_pipeline import process_and_send

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    db = Database(DB_PATH)
    await db.init()

    # Make db available to handlers via middleware (or inject)
    # Simple approach: pass db as a dependency using aiogram's built-in extra
    dp["db"] = db

    # Set bot commands list
    await bot.set_my_commands([
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="jobs", description="Get current jobs"),
        BotCommand(command="subscribe", description="Subscribe to job alerts"),
        BotCommand(command="unsubscribe", description="Manage subscriptions"),
        BotCommand(command="settings", description="View settings"),
    ])

    # Background scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: process_and_send(bot, db),
        "interval",
        minutes=FETCH_INTERVAL_MINUTES,
        id="fetch_jobs",
        replace_existing=True,
    )
    scheduler.start()

    logging.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())