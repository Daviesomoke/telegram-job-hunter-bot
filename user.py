








import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart

from db import Database
from config import MAX_JOBS_PER_MESSAGE
from job_pipeline import fetch_all_jobs
from helpers import format_job_message, clean_keywords

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, db: Database):
    await db.add_user(message.from_user.id, message.from_user.username or "unknown")
    await message.answer(
        "👋 <b>Welcome to JobBot!</b>\n\n"
        "I scan Reddit and RSS feeds for tech & remote jobs — "
        "then send matching alerts straight to you.\n\n"
        "<b>Get started:</b>\n"
        "• /jobs — See the latest jobs right now\n"
        "• /subscribe — Set up personalised job alerts\n"
        "• /help — All commands",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🤖 <b>JobBot Commands</b>\n\n"
        "/jobs — Fetch latest job listings\n"
        "/subscribe — Create a job alert\n"
        "  e.g. <code>/subscribe python, django --remote</code>\n"
        "  e.g. <code>/subscribe devops --location=Berlin</code>\n"
        "/unsubscribe — Remove an alert\n"
        "/settings — View your active alerts\n\n"
        "<b>Tips:</b>\n"
        "• Separate keywords with commas\n"
        "• <code>--remote</code> = remote jobs only\n"
        "• <code>--location=City</code> = filter by city\n"
        "• Alerts run every 10 minutes automatically",
        parse_mode="HTML"
    )


@router.message(Command("jobs"))
async def cmd_jobs(message: types.Message):
    status = await message.answer("🔍 Fetching latest jobs, please wait…")
    jobs = await fetch_all_jobs()
    if not jobs:
        await status.edit_text("😕 No jobs found right now. Try again in a few minutes.")
        return
    await status.delete()
    shown = jobs[:MAX_JOBS_PER_MESSAGE]
    text = "\n\n".join(format_job_message(j) for j in shown)
    await message.answer(
        f"💼 <b>Latest {len(shown)} Jobs</b>\n\n{text}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    if len(jobs) > MAX_JOBS_PER_MESSAGE:
        await message.answer(
            f"ℹ️ Showing {len(shown)} of {len(jobs)} jobs. "
            "Use /subscribe to get all matching alerts automatically."
        )


@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message, db: Database):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📌 <b>How to subscribe:</b>\n\n"
            "<code>/subscribe python, flask</code>\n"
            "<code>/subscribe react --remote</code>\n"
            "<code>/subscribe devops --location=London</code>",
            parse_mode="HTML"
        )
        return

    params = args[1]
    keywords = params
    remote_only = False
    location = None

    if "--remote" in params:
        remote_only = True
        keywords = keywords.replace("--remote", "").strip()

    for part in params.split():
        if part.startswith("--location="):
            location = part.split("=", 1)[1].strip()
            keywords = keywords.replace(part, "").strip()

    keywords = clean_keywords(keywords)
    if not keywords:
        await message.answer("⚠️ Please include at least one keyword.\nExample: <code>/subscribe python remote</code>", parse_mode="HTML")
        return

    existing = await db.get_subscriptions(message.from_user.id)
    for _, kw, _, _ in existing:
        if kw.lower() == keywords.lower():
            await message.answer("ℹ️ You already have an alert for those keywords.")
            return

    await db.add_subscription(message.from_user.id, keywords, remote_only, location)
    parts = [f"✅ <b>Alert created!</b>", f"🔑 Keywords: <code>{keywords}</code>"]
    if remote_only:
        parts.append("🌍 Remote only: Yes")
    if location:
        parts.append(f"📍 Location: {location}")
    parts.append("\nYou'll get notified when matching jobs are found.")
    await message.answer("\n".join(parts), parse_mode="HTML")


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: types.Message, db: Database):
    subs = await db.get_subscriptions(message.from_user.id)
    if not subs:
        await message.answer("You have no active alerts. Use /subscribe to create one.")
        return
    kb = []
    for sub_id, keywords, remote, loc in subs:
        label = keywords
        if remote:
            label += " 🌍"
        if loc:
            label += f" 📍{loc}"
        kb.append([types.InlineKeyboardButton(text=f"❌ {label}", callback_data=f"unsub_{sub_id}")])
    kb.append([types.InlineKeyboardButton(text="Cancel", callback_data="unsub_cancel")])
    await message.answer(
        "🗑 <b>Tap an alert to remove it:</b>",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("unsub_"))
async def cb_unsubscribe(callback: types.CallbackQuery, db: Database):
    if callback.data == "unsub_cancel":
        await callback.message.delete()
        await callback.answer()
        return
    sub_id = int(callback.data.split("_")[1])
    await db.remove_subscription(callback.from_user.id, sub_id)
    await callback.answer("✅ Alert removed!")
    await callback.message.delete()


@router.message(Command("settings"))
async def cmd_settings(message: types.Message, db: Database):
    subs = await db.get_subscriptions(message.from_user.id)
    if not subs:
        await message.answer("⚙️ <b>Your Settings</b>\n\nNo active alerts yet.\nUse /subscribe to create one.", parse_mode="HTML")
        return
    lines = ["⚙️ <b>Your Active Alerts</b>\n"]
    for i, (sub_id, keywords, remote, loc) in enumerate(subs, 1):
        line = f"{i}. <code>{keywords}</code>"
        if remote:
            line += " 🌍"
        if loc:
            line += f" 📍{loc}"
        lines.append(line)
    lines.append("\nUse /unsubscribe to remove any alert.")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message()
async def unknown_message(message: types.Message):
    await message.answer("I didn't understand that. Try /help to see what I can do.")