









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
    picking_roles    = State()
    picking_location = State()
    typing_location  = State()


# ── helpers ───────────────────────────────────────────────────────────────────

def build_role_keyboard(selected: list[str]) -> types.InlineKeyboardMarkup:
    """Build the role picker keyboard, ticked roles show a checkmark."""
    kb = []
    for category, roles in ROLE_CATEGORIES.items():
        kb.append([types.InlineKeyboardButton(
            text=category,
            callback_data="noop"
        )])
        row = []
        for role in roles:
            tick  = "✓ " if role in selected else ""
            row.append(types.InlineKeyboardButton(
                text=f"{tick}{role}",
                callback_data=f"toggle_{role}"
            ))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)

    # Bottom action bar
    if selected:
        kb.append([
            types.InlineKeyboardButton(
                text=f"Continue with {len(selected)} role(s)",
                callback_data="roles_done"
            )
        ])
        kb.append([
            types.InlineKeyboardButton(text="Clear all", callback_data="roles_clear"),
            types.InlineKeyboardButton(text="Cancel",    callback_data="sub_cancel"),
        ])
    else:
        kb.append([types.InlineKeyboardButton(text="Cancel", callback_data="sub_cancel")])

    return types.InlineKeyboardMarkup(inline_keyboard=kb)


def selected_roles_text(selected: list[str]) -> str:
    if not selected:
        return "None selected yet — tap roles below to pick them."
    return "Selected: " + ", ".join(selected)


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: types.Message, db: Database, state: FSMContext):
    await state.clear()
    await db.add_user(message.from_user.id, message.from_user.username or "unknown")
    name = message.from_user.first_name or "there"
    await message.answer(
        f"Hey {name}, welcome to Job Hunter.\n\n"
        "I track remote tech jobs across Reddit, RemoteOK, Himalayas, Lever and more "
        "then ping you only when something matches what you're looking for.\n\n"
        "Commands:\n"
        "/jobs — browse latest openings\n"
        "/subscribe — set up job alerts\n"
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
        "/subscribe — pick as many roles as you want, set a location, done\n"
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
            "Use /subscribe to get all matching results sent automatically."
        )


# ── /subscribe — Step 1: pick roles (multi-select) ────────────────────────────

@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(selected=[])
    await message.answer(
        "Tap as many roles as you want. Tap again to deselect.\n"
        "When you're done, tap Continue.",
        reply_markup=build_role_keyboard([])
    )
    await state.set_state(SubscribeFlow.picking_roles)


@router.callback_query(F.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_"), SubscribeFlow.picking_roles)
async def cb_toggle_role(callback: types.CallbackQuery, state: FSMContext):
    role = callback.data.replace("toggle_", "")
    data = await state.get_data()
    selected: list = list(data.get("selected", []))

    if role in selected:
        selected.remove(role)
        await callback.answer(f"Removed: {role}")
    else:
        selected.append(role)
        await callback.answer(f"Added: {role}")

    await state.update_data(selected=selected)

    # Update keyboard in place
    try:
        await callback.message.edit_text(
            f"Tap as many roles as you want. Tap again to deselect.\n"
            f"When you're done, tap Continue.\n\n"
            f"{selected_roles_text(selected)}",
            reply_markup=build_role_keyboard(selected)
        )
    except Exception:
        pass  # message unchanged, ignore


@router.callback_query(F.data == "roles_clear", SubscribeFlow.picking_roles)
async def cb_roles_clear(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(selected=[])
    await callback.message.edit_text(
        "Tap as many roles as you want. Tap again to deselect.\n"
        "When you're done, tap Continue.\n\n"
        "None selected yet — tap roles below to pick them.",
        reply_markup=build_role_keyboard([])
    )
    await callback.answer("Cleared")


# ── Step 2: pick location ─────────────────────────────────────────────────────

@router.callback_query(F.data == "roles_done", SubscribeFlow.picking_roles)
async def cb_roles_done(callback: types.CallbackQuery, state: FSMContext):
    data     = await state.get_data()
    selected = data.get("selected", [])

    if not selected:
        await callback.answer("Pick at least one role first.", show_alert=True)
        return

    roles_text = "\n".join(f"  {r}" for r in selected)
    await callback.message.edit_text(
        f"Roles selected:\n{roles_text}\n\n"
        "Where do you want to work?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Remote only",             callback_data="loc_remote")],
            [types.InlineKeyboardButton(text="Worldwide (any location)", callback_data="loc_worldwide")],
            [types.InlineKeyboardButton(text="Specific city or country", callback_data="loc_custom")],
            [types.InlineKeyboardButton(text="Back",                    callback_data="back_to_roles")],
        ])
    )
    await state.set_state(SubscribeFlow.picking_location)
    await callback.answer()


@router.callback_query(F.data == "back_to_roles")
async def cb_back_to_roles(callback: types.CallbackQuery, state: FSMContext):
    data     = await state.get_data()
    selected = data.get("selected", [])
    await callback.message.edit_text(
        "Tap as many roles as you want. Tap again to deselect.\n"
        "When you're done, tap Continue.\n\n"
        f"{selected_roles_text(selected)}",
        reply_markup=build_role_keyboard(selected)
    )
    await state.set_state(SubscribeFlow.picking_roles)
    await callback.answer()


@router.callback_query(F.data.startswith("loc_"), SubscribeFlow.picking_location)
async def cb_location_picked(callback: types.CallbackQuery, state: FSMContext, db: Database):
    choice = callback.data.replace("loc_", "")

    if choice == "custom":
        await callback.message.edit_text(
            "Type the city or country you want.\n"
            "Example: London, Kenya, Germany, New York"
        )
        await state.set_state(SubscribeFlow.typing_location)
        await callback.answer()
        return

    remote_only = choice == "remote"
    location    = None
    await _save_all_subscriptions(callback.message, state, db,
                                   callback.from_user.id, remote_only, location)
    await callback.answer()


@router.message(SubscribeFlow.typing_location)
async def receive_custom_location(message: types.Message, state: FSMContext, db: Database):
    location = message.text.strip()
    await _save_all_subscriptions(message, state, db,
                                   message.from_user.id, remote_only=False, location=location)


# ── save all selected roles as individual subscriptions ───────────────────────

async def _save_all_subscriptions(message, state: FSMContext, db: Database,
                                   user_id: int, remote_only: bool, location):
    data     = await state.get_data()
    selected = data.get("selected", [])

    existing_subs = await db.get_subscriptions(user_id)
    existing_kws  = [kw.lower() for _, kw, _, _ in existing_subs]

    saved    = []
    skipped  = []

    for role in selected:
        if role.lower() in existing_kws:
            skipped.append(role)
        else:
            await db.add_subscription(user_id, role, remote_only, location)
            saved.append(role)

    await state.clear()

    loc_label = "remote only" if remote_only else (location or "worldwide")

    lines = []
    if saved:
        lines.append(f"<b>Alerts created</b> ({loc_label}):\n")
        for r in saved:
            lines.append(f"  {r}")
    if skipped:
        lines.append(f"\nAlready active (skipped):\n")
        for r in skipped:
            lines.append(f"  {r}")

    lines.append("\nI'll message you as soon as matching jobs come in.")
    lines.append("Use /subscribe again to add more roles.")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ── cancel ────────────────────────────────────────────────────────────────────

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


# ── catch unknown ─────────────────────────────────────────────────────────────

@router.message()
async def unknown_message(message: types.Message, state: FSMContext):
    if await state.get_state():
        return
    await message.answer("Try /help to see what I can do.")