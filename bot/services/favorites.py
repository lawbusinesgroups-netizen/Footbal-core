from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import database as db
from bot.auth import require_auth
from bot.locales import t
from bot.keyboards import favorites_list_keyboard, main_menu_keyboard
from bot.services import api_football
from bot.handlers.games import render_game_menu

router = Router()


@router.callback_query(F.data.regexp(r"^fav:(add|del):\d+:\d+$"))
async def toggle_favorite(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    _, action, team_id_str, fixture_id_str = callback.data.split(":")
    team_id = int(team_id_str)
    fixture_id = int(fixture_id_str)

    if action == "add":
        meta = await api_football.get_fixture_meta(fixture_id)
        if meta and meta["home_id"] == team_id:
            team_name = meta["home"]
        elif meta and meta["away_id"] == team_id:
            team_name = meta["away"]
        else:
            team_name = str(team_id)
        await db.add_favorite(callback.from_user.id, team_id, team_name)
        await callback.answer(t(lang, "fav_added"))
    else:
        await db.remove_favorite(callback.from_user.id, team_id)
        await callback.answer(t(lang, "fav_removed"))

    await render_game_menu(callback, lang, fixture_id)


@router.callback_query(F.data == "menu:favorites")
async def show_favorites(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    await callback.answer()
    await _render_favorites_list(callback, lang)


@router.callback_query(F.data.regexp(r"^fav:rm:\d+$"))
async def remove_favorite_from_list(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    team_id = int(callback.data.split(":", 2)[2])
    await db.remove_favorite(callback.from_user.id, team_id)
    await callback.answer(t(lang, "fav_removed"))
    await _render_favorites_list(callback, lang)


async def _render_favorites_list(callback: CallbackQuery, lang: str) -> None:
    favorites = await db.list_favorites(callback.from_user.id)
    if not favorites:
        await callback.message.edit_text(
            t(lang, "no_favorites"), reply_markup=main_menu_keyboard(lang)
        )
        return
    await callback.message.edit_text(
        t(lang, "favorites_header"), reply_markup=favorites_list_keyboard(lang, favorites)
    )
