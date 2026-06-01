







import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import Database
from config import MAX_JOBS_PER_MESSAGE, ROLE_CATEGORIES
from job_pipeline import fetch_all_jobs
from helpers import format_job_message, clean_keywords

logger = logging.getLogger(__name__)
router = Router()


class SubscribeFlow(StatesGroup):
    picking_role     = State()
    picking_location = State()
    confirming       = State()


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: types.Message, db: Database, state: FSMContext):
    await state.clear()
    await db.add_user(message.from_user.id, message.from_user.username or "unknown")
    name = message.from_user.first_name or "there"
    await message.answer(
        f"Hey {name}, welcome to Job Hunter.\n\n"
        "I track remote tech jobs across Reddit, RemoteOK, Himalayas, Lever and more "
        "— then ping you only when something matches what you're looking for.\n\n"
        "Commands:\n"
        "/jobs — browse latest openings\n"
        "/subscribe — set up a job alert\n"
        "/settings — see your active alerts\n"
        "/unsubscribe — remove an alert\n"
        "/help — how everything works"
    )


# ── /help ─────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Job Hunter monitors 100+ sources every 10 minutes and sends "
        "you only the jobs that match your role and preferences.\n\n"
        "/subscribe — pick a role, set remote or location filter, done\n"
        "/jobs — see what's available right now\n"
        "/settings — check what alerts you have running\n"
        "/unsubscribe — delete any alert\n\n"
        "All jobs are remote unless you specify a location. "
        "You can have multiple alerts running at the same time."
    )


# ── /jobs ─────────────────────────────────────────────────────────────────────

@router.message(Command("jobs"))
async def cmd_jobs(message: types.Message):
    msg = await message.answer("Searching across all sources...")
    jobs = await fetch_all_jobs()

    if not jobs:
        await msg.edit_text("Nothing found right now. Try again in a few minutes.")
        return

    await msg.delete()
    shown = jobs[:MAX_JOBS_PER_MESSAGE]
    text  = "\n\n".join(format_job_message(j) for j in shown)

    await message.answer(
        f"<b>Latest jobs</b> ({len(shown)} of {len(jobs)} found)\n\n{text}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    if len(jobs) > MAX_JOBS_PER_MESSAGE:
        await message.answer(
            f"Use /subscribe to get all matching results sent to you automatically."
        )


# ── /subscribe — Step 1: pick a role ─────────────────────────────────────────

@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message, state: FSMContext):
    await state.clear()

    # Build role buttons from config categories
    kb = []
    for category, roles in ROLE_CATEGORIES.items():
        # Category header button (not tappable, just a label)
        kb.append([types.InlineKeyboardButton(
            text=f"--- {category} ---",
            callback_data="noop"
        )])
        # Role buttons in pairs
        row = []
        for role in roles:
            row.append(types.InlineKeyboardButton(
                text=role,
                callback_data=f"role_{role}"
            ))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)

    kb.append([types.InlineKeyboardButton(text="Cancel", callback_data="sub_cancel")])

    await message.answer(
        "What kind of role are you looking for?\n"
        "Tap one to set up an alert for it.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await state.set_state(SubscribeFlow.picking_role)


@router.callback_query(F.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()


# ── Step 2: pick remote or location ──────────────────────────────────────────

@router.callback_query(F.data.startswith("role_"), SubscribeFlow.picking_role)
async def cb_role_picked(callback: types.CallbackQuery, state: FSMContext):
    role = callback.data.replace("role_", "")
    await state.update_data(role=role)
    await callback.message.edit_text(
        f"Role: <b>{role}</b>\n\n"
        "Where do you want to work?",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Remote only", callback_data="loc_remote")],
            [types.InlineKeyboardButton(text="Worldwide (remote + onsite)", callback_data="loc_worldwide")],
            [types.InlineKeyboardButton(text="Type a city or country", callback_data="loc_custom")],
            [types.InlineKeyboardButton(text="Back", callback_data="sub_back_role")],
        ])
    )
    await state.set_state(SubscribeFlow.picking_location)
    await callback.answer()


@router.callback_query(F.data == "sub_back_role")
async def cb_back_to_role(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SubscribeFlow.picking_role)
    await cmd_subscribe(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("loc_"), SubscribeFlow.picking_location)
async def cb_location_picked(callback: types.CallbackQuery, state: FSMContext):
    loc_choice = callback.data.replace("loc_", "")

    if loc_choice == "custom":
        await callback.message.edit_text(
            "Type the city or country you want to filter by.\n"
            "Example: London, Kenya, Germany"
        )
        await state.set_state(SubscribeFlow.confirming)
        await callback.answer()
        return

    remote_only = loc_choice == "remote"
    location    = None if loc_choice in ("remote", "worldwide") else None
    await _confirm_subscription(callback.message, state, remote_only, location)
    await callback.answer()


@router.message(SubscribeFlow.confirming)
async def receive_custom_location(message: types.Message, state: FSMContext):
    location = message.text.strip()
    await _confirm_subscription(message, state, remote_only=False, location=location)


async def _confirm_subscription(message, state: FSMContext, remote_only: bool, location):
    data = await state.get_data()
    role = data.get("role", "")

    loc_label = "Remote only" if remote_only else (location or "Worldwide")

    await message.answer(
        f"Role: <b>{role}</b>\n"
        f"Location: {loc_label}\n\n"
        "Set up this alert?",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Yes, create alert", callback_data="sub_confirm"),
                types.InlineKeyboardButton(text="No, cancel",        callback_data="sub_cancel"),
            ]
        ])
    )
    await state.update_data(remote_only=remote_only, location=location)
    await state.set_state(SubscribeFlow.confirming)


@router.callback_query(F.data == "sub_confirm")
async def cb_confirm_subscription(callback: types.CallbackQuery, state: FSMContext, db: Database):
    data        = await state.get_data()
    role        = data.get("role", "")
    remote_only = data.get("remote_only", True)
    location    = data.get("location")

    # Check for duplicates
    existing = await db.get_subscriptions(callback.from_user.id)
    for _, kw, _, _ in existing:
        if kw.lower() == role.lower():
            await callback.message.edit_text(
                f"You already have an alert for <b>{role}</b>. "
                "Check /settings to see all your alerts.",
                parse_mode="HTML"
            )
            await state.clear()
            await callback.answer()
            return

    await db.add_subscription(callback.from_user.id, role, remote_only, location)

    loc_label = "Remote only" if remote_only else (location or "Worldwide")
    await callback.message.edit_text(
        f"Alert created.\n\n"
        f"Role: <b>{role}</b>\n"
        f"Location: {loc_label}\n\n"
        "I'll message you as soon as matching jobs come in. "
        "Use /subscribe again to add more roles.",
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "sub_cancel")
async def cb_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Cancelled. Use /subscribe whenever you're ready.")
    await callback.answer()


# ── /unsubscribe ──────────────────────────────────────────────────────────────

@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: types.Message, db: Database):
    subs = await db.get_subscriptions(message.from_user.id)
    if not subs:
        await message.answer("You have no active alerts. Use /subscribe to create one.")
        return

    kb = []
    for sub_id, keywords, remote, loc in subs:
        loc_label = "remote" if remote else (loc or "worldwide")
        kb.append([types.InlineKeyboardButton(
            text=f"{keywords}  ({loc_label})  [remove]",
            callback_data=f"unsub_{sub_id}"
        )])
    kb.append([types.InlineKeyboardButton(text="Done", callback_data="unsub_done")])

    await message.answer(
        "Your active alerts. Tap one to remove it.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
    )


@router.callback_query(F.data.startswith("unsub_"))
async def cb_unsubscribe(callback: types.CallbackQuery, db: Database):
    if callback.data == "unsub_done":
        await callback.message.delete()
        await callback.answer()
        return
    sub_id = int(callback.data.split("_")[1])
    await db.remove_subscription(callback.from_user.id, sub_id)
    await callback.answer("Removed.")
    await callback.message.delete()


# ── /settings ─────────────────────────────────────────────────────────────────

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, db: Database):
    subs = await db.get_subscriptions(message.from_user.id)
    if not subs:
        await message.answer(
            "No active alerts yet.\n"
            "Use /subscribe to set one up."
        )
        return

    lines = ["<b>Your active alerts</b>\n"]
    for i, (sub_id, keywords, remote, loc) in enumerate(subs, 1):
        loc_label = "remote only" if remote else (loc or "worldwide")
        lines.append(f"{i}. {keywords}  —  {loc_label}")

    lines.append("\nUse /unsubscribe to remove any of these.")
    await message.answer("\n".join(lines), parse_mode="HTML")


# ── catch unknown messages ────────────────────────────────────────────────────

@router.message()
async def unknown_message(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if current:
        return  # FSM is handling it
    await message.answer("Try /help to see what I can do.")