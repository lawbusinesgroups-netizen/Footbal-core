from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.locales import t, league_short


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_games"), callback_data="menu:games")],
            [InlineKeyboardButton(text=t(lang, "btn_favorites"), callback_data="menu:favorites")],
            [InlineKeyboardButton(text=t(lang, "btn_accuracy"), callback_data="menu:accuracy")],
        ]
    )


def league_filter_keyboard(lang: str, league_ids: list) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for lid in league_ids:
        row.append(InlineKeyboardButton(text=league_short(lang, lid), callback_data=f"gf:{lid}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t(lang, "btn_all_leagues"), callback_data="gf:all")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def games_list_keyboard(lang: str, fixtures: list) -> InlineKeyboardMarkup:
    rows = []
    for fx in fixtures:
        label = f"{fx['time']} | {fx['home']} vs {fx['away']}"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"game:{fx['id']}")]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="menu:games")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def game_menu_keyboard(
    lang: str,
    fixture_id: int,
    home_id: int,
    home_name: str,
    away_id: int,
    away_name: str,
    home_is_fav: bool,
    away_is_fav: bool,
) -> InlineKeyboardMarkup:
    def _fav_button(team_id: int, team_name: str, is_fav: bool) -> InlineKeyboardButton:
        if is_fav:
            return InlineKeyboardButton(
                text=f"✅ {team_name}", callback_data=f"fav:del:{team_id}:{fixture_id}"
            )
        return InlineKeyboardButton(
            text=f"⭐ {team_name}", callback_data=f"fav:add:{team_id}:{fixture_id}"
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_stats"), callback_data=f"stats:{fixture_id}")],
            [InlineKeyboardButton(text=t(lang, "btn_ai"), callback_data=f"ai:{fixture_id}")],
            [
                _fav_button(home_id, home_name, home_is_fav),
                _fav_button(away_id, away_name, away_is_fav),
            ],
            [InlineKeyboardButton(text=t(lang, "btn_back_to_games"), callback_data="menu:games")],
        ]
    )


def favorites_list_keyboard(lang: str, favorites: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"❌ {fav['team_name']}", callback_data=f"fav:rm:{fav['team_id']}")]
        for fav in favorites
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_game_keyboard(lang: str, fixture_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"game:{fixture_id}")]
        ]
    )
