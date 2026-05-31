







import asyncio
import logging
import sys
import os
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

# Flat imports — no subfolders needed
from config import BOT_TOKEN, DB_PATH, FETCH_INTERVAL_MINUTES, PORT
from db import Database
from user import router
from job_pipeline import process_and_send

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def health_check(request):
    return web.Response(text="OK", status=200)


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health check server on port {PORT}")
    return runner


async def main():
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set. Exiting.")
        sys.exit(1)

    logger.info("Starting JobBot...")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    db = Database(DB_PATH)
    await db.init()
    logger.info("Database ready")

    @dp.update.middleware()
    async def inject_db(handler, event: Update, data: dict):
        data["db"] = db
        return await handler(event, data)

    await bot.set_my_commands([
        BotCommand(command="start",       description="🚀 Start the bot"),
        BotCommand(command="jobs",        description="💼 See latest jobs now"),
        BotCommand(command="subscribe",   description="🔔 Create a job alert"),
        BotCommand(command="unsubscribe", description="🗑 Remove a job alert"),
        BotCommand(command="settings",    description="⚙️ View your alerts"),
        BotCommand(command="help",        description="❓ How to use the bot"),
    ])

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        process_and_send,
        trigger="interval",
        minutes=FETCH_INTERVAL_MINUTES,
        args=[bot, db],
        id="job_pipeline",
        misfire_grace_time=60,
        coalesce=True,
    )
    scheduler.start()
    logger.info(f"Scheduler: every {FETCH_INTERVAL_MINUTES} minutes")

    runner = await start_health_server()

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ JobBot is running!")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await runner.cleanup()
        await bot.session.close()
        logger.info("Bot shut down cleanly")


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())