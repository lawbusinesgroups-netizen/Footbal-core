from aiogram import Router, F
from aiogram.filters import StateFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot import database as db
from bot.auth import AuthStates
from bot.config import ACCESS_PASSWORD
from bot.locales import t
from bot.keyboards import language_keyboard, main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await db.ensure_user(message.from_user.id)
    await message.answer(t("ru", "choose_language"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split(":", 1)[1]
    await db.set_language(callback.from_user.id, lang)

    if await db.is_authenticated(callback.from_user.id):
        await state.clear()
        await callback.message.edit_text(
            t(lang, "main_menu"), reply_markup=main_menu_keyboard(lang)
        )
    else:
        await state.set_state(AuthStates.waiting_password)
        await callback.message.edit_text(t(lang, "ask_password"))
    await callback.answer()


@router.message(StateFilter(AuthStates.waiting_password))
async def on_password_entered(message: Message, state: FSMContext) -> None:
    lang = await db.get_language(message.from_user.id)
    if message.text == ACCESS_PASSWORD:
        await db.set_authenticated(message.from_user.id, True)
        await state.clear()
        await message.answer(t(lang, "access_granted"))
        await message.answer(t(lang, "main_menu"), reply_markup=main_menu_keyboard(lang))
    else:
        await message.answer(t(lang, "wrong_password"))


@router.callback_query(F.data == "menu:main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await db.get_language(callback.from_user.id)
    await callback.message.edit_text(t(lang, "main_menu"), reply_markup=main_menu_keyboard(lang))
    await callback.answer()
