






import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
from contextlib import suppress

from config import BOT_TOKEN, DB_PATH, FETCH_INTERVAL_MINUTES, PORT
from database.db import Database
from handlers.user import router
from services.job_pipeline import process_and_send

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def health_check(request):
    return web.Response(text="Bot is running")

async def main():
    try:
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN is not set!")
            sys.exit(1)
        
        logger.info("Starting bot...")
        
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
        
        db = Database(DB_PATH)
        await db.init()
        logger.info("Database initialized")
        
        @dp.update.middleware()
        async def inject_db(handler, event: Update, data: dict):
            data["db"] = db
            return await handler(event, data)
        
        await bot.set_my_commands([
            BotCommand(command="start", description="🚀 Start"),
            BotCommand(command="jobs", description="💼 Latest jobs"),
            BotCommand(command="subscribe", description="🔔 Job alerts"),
            BotCommand(command="unsubscribe", description="❌ Remove alerts"),
            BotCommand(command="settings", description="⚙️ Settings"),
        ])
        
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            process_and_send,
            "interval",
            minutes=FETCH_INTERVAL_MINUTES,
            args=[bot, db],
            id="fetch_jobs",
        )
        scheduler.start()
        logger.info("Scheduler started")
        
        # Health check server for Render
        app = web.Application()
        app.router.add_get('/', health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        logger.info(f"Health check on port {PORT}")
        
        logger.info("Bot is running!")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())