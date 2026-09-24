from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import database as db
from bot.auth import require_auth
from bot.locales import t
from bot.keyboards import back_to_game_keyboard, main_menu_keyboard
from bot.services import api_football
from bot.services.groq_service import analyze_match, extract_pick, strip_pick_tag
from bot.handlers.stats import build_stats_text

router = Router()


@router.callback_query(F.data.startswith("ai:"))
async def show_ai_analysis(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    fixture_id = int(callback.data.split(":", 1)[1])
    await callback.answer()
    await callback.message.edit_text(t(lang, "loading_ai"))

    try:
        stats_text = await build_stats_text(lang, fixture_id)
        if not stats_text:
            raise ValueError("no stats")
        analysis = await analyze_match(lang, stats_text)
    except Exception:
        await callback.message.edit_text(
            t(lang, "error_api"), reply_markup=main_menu_keyboard(lang)
        )
        return

    pick = extract_pick(analysis)
    if pick:
        meta = await api_football.get_fixture_meta(fixture_id)
        if meta:
            await db.save_prediction(
                fixture_id, meta["home"], meta["away"], pick, meta["timestamp"]
            )

    final_text = strip_pick_tag(analysis) + t(lang, "ai_disclaimer")
    await callback.message.edit_text(
        final_text, reply_markup=back_to_game_keyboard(lang, fixture_id)
    )
