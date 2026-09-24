from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import database as db
from bot.auth import require_auth
from bot.locales import t
from bot.keyboards import main_menu_keyboard

router = Router()


@router.callback_query(F.data == "menu:accuracy")
async def show_accuracy(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    await callback.answer()
    stats = await db.get_accuracy_stats()

    if not stats["total"]:
        await callback.message.edit_text(
            t(lang, "accuracy_none"), reply_markup=main_menu_keyboard(lang)
        )
        return

    text = t(lang, "accuracy_header").format(
        correct=stats["correct"], total=stats["total"], pct=stats["accuracy_pct"]
    )
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(lang))
