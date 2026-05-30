







from aiogram import Router, types
from aiogram.filters import Command
from database.db import Database
from config import MAX_JOBS_PER_MESSAGE
from services.job_pipeline import fetch_all_jobs
from utils.helpers import format_job_message, clean_keywords

router = Router()

@router.message(Command("start"))
async def start(message: types.Message, db: Database):
    await db.add_user(message.from_user.id, message.from_user.username or "unknown")
    await message.answer(
        "👋 *Welcome to JobBot!*\n\n"
        "I fetch remote & tech jobs from Reddit, LinkedIn, RSS feeds, and more.\n\n"
        "*Quick start:*\n"
        "• /jobs — See latest jobs\n"
        "• /subscribe python remote — Get alerts for Python remote jobs\n"
        "• /help — See all commands",
        parse_mode="Markdown"
    )

@router.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "🤖 *JobBot Commands*\n\n"
        "*/jobs* — Get latest job listings\n"
        "*/subscribe* — Set up job alerts\n"
        "  Example: `/subscribe python, remote`\n"
        "  Flags: `--remote` (remote only)\n"
        "  Flags: `--location=Berlin`\n"
        "*/unsubscribe* — Remove alerts\n"
        "*/settings* — View your settings\n\n"
        "*Tips:*\n"
        "• Use commas for multiple keywords\n"
        "• Add `--remote` for remote-only jobs\n"
        "• Job alerts are sent automatically",
        parse_mode="Markdown"
    )

@router.message(Command("jobs"))
async def manual_jobs(message: types.Message):
    await message.answer("🔍 Fetching latest jobs...")
    jobs = await fetch_all_jobs()
    if not jobs:
        await message.answer("No jobs found right now. Try again later.")
        return
    
    for i in range(0, min(len(jobs), MAX_JOBS_PER_MESSAGE), MAX_JOBS_PER_MESSAGE):
        chunk = jobs[i:i+MAX_JOBS_PER_MESSAGE]
        text = "\n\n".join(format_job_message(j) for j in chunk)
        await message.answer(text, disable_web_page_preview=True)

@router.message(Command("subscribe"))
async def subscribe(message: types.Message, db: Database):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: `/subscribe keywords`\n\n"
            "Example: `/subscribe python, remote --remote`\n"
            "Example: `/subscribe devops --location=London`",
            parse_mode="Markdown"
        )
        return
    
    params = args[1]
    keywords = params
    remote_only = False
    location = None
    
    if "--remote" in params:
        remote_only = True
        keywords = keywords.replace("--remote", "").strip()
    
    if "--location=" in params:
        for part in params.split():
            if part.startswith("--location="):
                location = part.split("=", 1)[1]
                keywords = keywords.replace(part, "").strip()
    
    keywords = clean_keywords(keywords)
    
    if not keywords:
        await message.answer("Please provide at least one keyword.")
        return
    
    await db.add_subscription(message.from_user.id, keywords, remote_only, location)
    
    confirmation = f"✅ *Subscribed!*\nKeywords: `{keywords}`"
    if remote_only:
        confirmation += "\n🌍 Remote only"
    if location:
        confirmation += f"\n📍 Location: {location}"
    
    await message.answer(confirmation, parse_mode="Markdown")

@router.message(Command("unsubscribe"))
async def unsubscribe(message: types.Message, db: Database):
    subs = await db.get_subscriptions(message.from_user.id)
    if not subs:
        await message.answer("You have no subscriptions. Use /subscribe to create one.")
        return
    
    kb = []
    for sub_id, keywords, remote, loc in subs:
        desc = keywords
        if remote:
            desc += " 🌍"
        if loc:
            desc += f" 📍{loc}"
        kb.append([types.InlineKeyboardButton(
            text=f"❌ {desc}", 
            callback_data=f"unsub_{sub_id}"
        )])
    
    await message.answer(
        "Your subscriptions — tap to remove:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )

@router.callback_query(lambda c: c.data.startswith("unsub_"))
async def process_unsub(callback: types.CallbackQuery, db: Database):
    sub_id = int(callback.data.split("_")[1])
    await db.remove_subscription(callback.from_user.id, sub_id)
    await callback.answer("✅ Removed!")
    await callback.message.delete()

@router.message(Command("settings"))
async def settings(message: types.Message, db: Database):
    subs = await db.get_subscriptions(message.from_user.id)
    count = len(subs)
    await message.answer(
        f"⚙️ *Your Settings*\n\n"
        f"Active subscriptions: *{count}*\n\n"
        f"Use /subscribe to add alerts\n"
        f"Use /unsubscribe to manage them",
        parse_mode="Markdown"
    )