from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import config
from bot import database as db
from bot.auth import require_auth
from bot.locales import t
from bot.keyboards import (
    games_list_keyboard,
    league_filter_keyboard,
    game_menu_keyboard,
    main_menu_keyboard,
)
from bot.services import api_football

router = Router()


@router.callback_query(F.data == "menu:games")
async def show_games(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    await callback.answer()
    await callback.message.edit_text(t(lang, "loading_games"))

    try:
        fixtures = await api_football.get_fixtures_next_24h()
    except Exception:
        await callback.message.edit_text(
            t(lang, "error_api"), reply_markup=main_menu_keyboard(lang)
        )
        return

    if not fixtures:
        await callback.message.edit_text(
            t(lang, "no_games"), reply_markup=main_menu_keyboard(lang)
        )
        return

    # Leagues actually present today, in config.LEAGUES order.
    present_ids = {fx["league_id"] for fx in fixtures}
    league_ids = [lid for lid in config.LEAGUES if lid in present_ids]

    await callback.message.edit_text(
        t(lang, "choose_league_filter"),
        reply_markup=league_filter_keyboard(lang, league_ids),
    )


@router.callback_query(F.data.startswith("gf:"))
async def show_filtered_games(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    await callback.answer()

    choice = callback.data.split(":", 1)[1]

    try:
        fixtures = await api_football.get_fixtures_next_24h()
    except Exception:
        await callback.message.edit_text(
            t(lang, "error_api"), reply_markup=main_menu_keyboard(lang)
        )
        return

    if choice != "all":
        league_id = int(choice)
        fixtures = [fx for fx in fixtures if fx["league_id"] == league_id]

    if not fixtures:
        await callback.message.edit_text(
            t(lang, "no_games_league"), reply_markup=main_menu_keyboard(lang)
        )
        return

    # Telegram inline keyboards get unwieldy beyond ~30 rows; cap the list.
    fixtures = fixtures[:30]
    await callback.message.edit_text(
        t(lang, "choose_game"), reply_markup=games_list_keyboard(lang, fixtures)
    )


@router.callback_query(F.data.startswith("game:"))
async def show_game_menu(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    fixture_id = int(callback.data.split(":", 1)[1])
    await callback.answer()
    await render_game_menu(callback, lang, fixture_id)


async def render_game_menu(callback: CallbackQuery, lang: str, fixture_id: int) -> None:
    meta = await api_football.get_fixture_meta(fixture_id)
    if not meta:
        await callback.message.edit_text(
            t(lang, "error_api"), reply_markup=main_menu_keyboard(lang)
        )
        return

    home_fav = await db.is_favorite(callback.from_user.id, meta["home_id"])
    away_fav = await db.is_favorite(callback.from_user.id, meta["away_id"])

    title = f"⚽ {meta['home']} vs {meta['away']}\n🏆 {meta['league_name']}\n🕒 {meta['time']}"
    await callback.message.edit_text(
        f"{title}\n\n{t(lang, 'game_menu')}",
        reply_markup=game_menu_keyboard(
            lang,
            fixture_id,
            meta["home_id"],
            meta["home"],
            meta["away_id"],
            meta["away"],
            home_fav,
            away_fav,
        ),
    )
