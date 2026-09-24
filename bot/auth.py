from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from bot import database as db
from bot.locales import t


class AuthStates(StatesGroup):
    waiting_password = State()


async def require_auth(callback: CallbackQuery, lang: str, state: FSMContext) -> bool:
    """Common auth gate for callback handlers.

    Returns True if the user is authenticated and the caller should proceed.
    Otherwise answers the callback, arms AuthStates.waiting_password so the
    next text message the user sends is caught by start.on_password_entered,
    and prompts for the password. Without setting this state, a user whose
    FSM state was reset (e.g. bot restart, since MemoryStorage isn't
    persistent) would see "enter password" but typing it would go nowhere.
    """
    if await db.is_authenticated(callback.from_user.id):
        return True
    await callback.answer()
    await state.set_state(AuthStates.waiting_password)
    await callback.message.edit_text(t(lang, "ask_password"))
    return False
