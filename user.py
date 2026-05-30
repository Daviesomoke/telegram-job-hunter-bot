

















from aiogram import Router, types
from aiogram.filters import Command
from database.db import Database
from config import MAX_JOBS_PER_MESSAGE
from scrapers.base import Job
from services.job_pipeline import fetch_all_jobs
from utils.helpers import format_job_message

router = Router()

@router.message(Command("start"))
async def start(message: types.Message, db: Database):
    await db.add_user(message.from_user.id, message.from_user.username or "unknown")
    await message.answer(
        "👋 Welcome to JobBot!\n"
        "Use /subscribe to set up job alerts.\n"
        "Example: /subscribe python, remote\n"
        "Available commands: /jobs, /subscribe, /unsubscribe, /settings"
    )

@router.message(Command("jobs"))
async def manual_jobs(message: types.Message):
    # Fetch a quick batch (without dedup) for immediate preview
    jobs = await fetch_all_jobs()
    if not jobs:
        await message.answer("No jobs found right now.")
        return
    # Show first few
    for i in range(0, min(len(jobs), MAX_JOBS_PER_message), MAX_JOBS_PER_MESSAGE):
        chunk = jobs[i:i+MAX_JOBS_PER_MESSAGE]
        text = "\n\n".join(format_job_message(j) for j in chunk)
        await message.answer(text, disable_web_page_preview=True)

@router.message(Command("subscribe"))
async def subscribe(message: types.Message, db: Database):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /subscribe keywords, separated by commas\n"
                             "Optional flags: --remote --location=City\n"
                             "Example: /subscribe python, remote --remote")
        return
    params = args[1]
    keywords = params
    remote_only = False
    location = None
    # Simple flag parsing
    if "--remote" in params:
        remote_only = True
        keywords = keywords.replace("--remote", "").strip()
    if "--location=" in params:
        # extract location
        for part in params.split():
            if part.startswith("--location="):
                location = part.split("=", 1)[1]
                keywords = keywords.replace(part, "").strip()
    keywords = keywords.strip().rstrip(",")
    if not keywords:
        await message.answer("Please provide at least one keyword.")
        return
    await db.add_subscription(message.from_user.id, keywords, remote_only, location)
    await message.answer(f"✅ Subscribed to: {keywords}" +
                         (f" (remote only)" if remote_only else "") +
                         (f" in {location}" if location else ""))

@router.message(Command("unsubscribe"))
async def unsubscribe(message: types.Message, db: Database):
    subs = await db.get_subscriptions(message.from_user.id)
    if not subs:
        await message.answer("You have no subscriptions.")
        return
    # Build inline keyboard with subscription IDs
    kb = []
    for sub_id, keywords, remote, loc in subs:
        desc = keywords + (" (remote)" if remote else "") + (f" in {loc}" if loc else "")
        kb.append([types.InlineKeyboardButton(text=f"❌ {desc}", callback_data=f"unsub_{sub_id}")])
    await message.answer("Your subscriptions:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(lambda c: c.data.startswith("unsub_"))
async def process_unsub(callback: types.CallbackQuery, db: Database):
    sub_id = int(callback.data.split("_")[1])
    await db.remove_subscription(callback.from_user.id, sub_id)
    await callback.answer("Subscription removed.")
    await callback.message.edit_text("Subscription removed.")

@router.message(Command("settings"))
async def settings(message: types.Message):
    await message.answer("Settings: use /subscribe to manage alerts, /unsubscribe to remove.")