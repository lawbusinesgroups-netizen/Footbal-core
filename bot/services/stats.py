from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import config
from bot import database as db
from bot.auth import require_auth
from bot.locales import t
from bot.keyboards import back_to_game_keyboard, main_menu_keyboard
from bot.services import api_football, sportsdb
from bot.config import LAST_N_MATCHES

router = Router()

STAT_LABELS = {
    "ru": {
        "corners": "Угловые",
        "yellow_cards": "Жёлтые карточки",
        "red_cards": "Красные карточки",
        "shots_on_target": "Удары в створ",
        "shots_total": "Удары всего",
        "fouls": "Фолы",
        "offsides": "Офсайды",
        "possession_pct": "Владение мячом",
        "woodwork": "Попадания в штангу/перекладину",
    },
    "en": {
        "corners": "Corners",
        "yellow_cards": "Yellow cards",
        "red_cards": "Red cards",
        "shots_on_target": "Shots on target",
        "shots_total": "Total shots",
        "fouls": "Fouls",
        "offsides": "Offsides",
        "possession_pct": "Possession",
        "woodwork": "Hit woodwork",
    },
}

# Fixed display order; anything not listed here is appended afterwards.
STAT_ORDER = [
    "corners",
    "yellow_cards",
    "red_cards",
    "shots_on_target",
    "shots_total",
    "fouls",
    "offsides",
    "possession_pct",
    "woodwork",
]


def _format_form_summary(lang: str, summary: dict) -> str:
    labels = STAT_LABELS.get(lang, STAT_LABELS["ru"])
    averages = summary.get("averages", {})
    if not averages:
        return t(lang, "form_no_data")

    ordered_keys = [k for k in STAT_ORDER if k in averages]
    ordered_keys += [k for k in averages if k not in STAT_ORDER]

    lines = []
    for key in ordered_keys:
        label = labels.get(key, key)
        value = averages[key]
        suffix = "%" if key == "possession_pct" else ""
        lines.append(f"  • {label}: {value}{suffix}")
    return "\n".join(lines)


def _sum_cards(card_block: dict) -> int:
    total = 0
    for bucket in (card_block or {}).values():
        val = bucket.get("total")
        if val:
            total += val
    return total


def _team_summary(stats: dict) -> dict:
    fixtures = stats.get("fixtures", {})
    goals = stats.get("goals", {})
    cards = stats.get("cards", {})
    return {
        "played": fixtures.get("played", {}).get("total", "-"),
        "wins": fixtures.get("wins", {}).get("total", "-"),
        "draws": fixtures.get("draws", {}).get("total", "-"),
        "loses": fixtures.get("loses", {}).get("total", "-"),
        "goals_for": goals.get("for", {}).get("total", {}).get("total", "-"),
        "goals_against": goals.get("against", {}).get("total", {}).get("total", "-"),
        "yellow_cards": _sum_cards(cards.get("yellow")),
        "red_cards": _sum_cards(cards.get("red")),
        "form": stats.get("form", "-"),
        "clean_sheets": stats.get("clean_sheet", {}).get("total", "-"),
    }


async def build_stats_text(lang: str, fixture_id: int) -> str | None:
    meta = await api_football.get_fixture_meta(fixture_id)
    if not meta:
        return None

    home_stats_raw = await api_football.get_team_statistics(
        meta["home_id"], meta["league_id"], meta["season"]
    )
    away_stats_raw = await api_football.get_team_statistics(
        meta["away_id"], meta["league_id"], meta["season"]
    )
    h2h = await api_football.get_head_to_head(meta["home_id"], meta["away_id"])

    lines = [
        f"⚽ *{meta['home']} vs {meta['away']}*",
        f"🏆 {meta['league_name']} | 🕒 {meta['time']}",
        "",
    ]

    for label, stats_raw, team_name in (
        ("🏠" if lang == "en" else "🏠 " + meta["home"], home_stats_raw, meta["home"]),
        ("🚩" if lang == "en" else "🚩 " + meta["away"], away_stats_raw, meta["away"]),
    ):
        lines.append(f"*{team_name}*")
        if stats_raw:
            s = _team_summary(stats_raw)
            lines.append(
                f"  Игры: {s['played']} | П-Н-П: {s['wins']}-{s['draws']}-{s['loses']}"
                if lang == "ru"
                else f"  Played: {s['played']} | W-D-L: {s['wins']}-{s['draws']}-{s['loses']}"
            )
            lines.append(
                f"  Голы: {s['goals_for']}:{s['goals_against']} | Форма: {s['form']}"
                if lang == "ru"
                else f"  Goals: {s['goals_for']}:{s['goals_against']} | Form: {s['form']}"
            )
            lines.append(
                f"  🟨 {s['yellow_cards']} | 🟥 {s['red_cards']} | Сухие матчи: {s['clean_sheets']}"
                if lang == "ru"
                else f"  🟨 {s['yellow_cards']} | 🟥 {s['red_cards']} | Clean sheets: {s['clean_sheets']}"
            )
        else:
            try:
                form = await sportsdb.get_recent_form(team_name)
            except Exception:
                form = []
            if form:
                results = ", ".join(
                    f"{f['home']} {f['home_score']}:{f['away_score']} {f['away']}"
                    for f in form[:5]
                )
                lines.append(f"  {results}")
            else:
                lines.append(f"  {t(lang, 'stats_unavailable')}")

        try:
            form_summary = await api_football.get_last_n_form_summary(
                meta["home_id"] if team_name == meta["home"] else meta["away_id"]
            )
        except Exception:
            form_summary = {"matches_analyzed": 0, "averages": {}}

        lines.append(t(lang, "form_header").format(n=LAST_N_MATCHES))
        lines.append(_format_form_summary(lang, form_summary))

        low_data = (not stats_raw) or (
            form_summary.get("matches_analyzed", 0) < config.MIN_RELIABLE_MATCHES
        )
        if low_data:
            lines.append(t(lang, "low_data_note"))

        lines.append("")

    if h2h:
        lines.append("🔁 *Head-to-Head*")
        for game in h2h[:5]:
            lines.append(
                f"  {game['date']}: {game['home']} {game['home_goals']}:{game['away_goals']} {game['away']}"
            )
        lines.append("")

    lines.append(t(lang, "corners_note"))
    return "\n".join(lines)


@router.callback_query(F.data.startswith("stats:"))
async def show_stats(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await db.get_language(callback.from_user.id)
    if not await require_auth(callback, lang, state):
        return

    fixture_id = int(callback.data.split(":", 1)[1])
    await callback.answer()
    await callback.message.edit_text(t(lang, "loading_stats"))

    try:
        text = await build_stats_text(lang, fixture_id)
    except Exception:
        await callback.message.edit_text(
            t(lang, "error_api"), reply_markup=main_menu_keyboard(lang)
        )
        return

    if not text:
        await callback.message.edit_text(
            t(lang, "error_api"), reply_markup=main_menu_keyboard(lang)
        )
        return

    await callback.message.edit_text(
        text, reply_markup=back_to_game_keyboard(lang, fixture_id), parse_mode="Markdown"
    )
