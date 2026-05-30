








import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import suppress

from config import BOT_TOKEN, DB_PATH, FETCH_INTERVAL_MINUTES
from database.db import Database
from handlers.user import router
from services.job_pipeline import process_and_send

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    # Initialize database
    db = Database(DB_PATH)
    await db.init()
    logger.info("Database initialized")
    
    # Middleware to inject database into handlers
    from aiogram.types import Update
    
    @dp.update.middleware()
    async def inject_db(handler, event: Update, data: dict):
        data["db"] = db
        return await handler(event, data)
    
    # Set bot commands
    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 Start the bot"),
        BotCommand(command="help", description="❓ Get help"),
        BotCommand(command="jobs", description="💼 Get current jobs"),
        BotCommand(command="subscribe", description="🔔 Subscribe to alerts"),
        BotCommand(command="unsubscribe", description="❌ Manage subscriptions"),
        BotCommand(command="settings", description="⚙️ View settings"),
    ])
    
    # Setup scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        process_and_send,
        "interval",
        minutes=FETCH_INTERVAL_MINUTES,
        args=[bot, db],
        id="fetch_jobs",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started (every {FETCH_INTERVAL_MINUTES} minutes)")
    
    # Start bot
    logger.info("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())