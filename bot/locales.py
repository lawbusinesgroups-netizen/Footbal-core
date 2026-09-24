TEXTS = {
    "ru": {
        "choose_language": "Выберите язык / Choose your language:",
        "ask_password": "Введите пароль для доступа к боту:",
        "wrong_password": "❌ Неверный пароль. Попробуйте ещё раз:",
        "access_granted": "✅ Доступ разрешён! Добро пожаловать.",
        "main_menu": "Главное меню. Выберите действие:",
        "btn_games": "⚽ Игры (24 часа)",
        "btn_stats": "📊 Статистика",
        "btn_ai": "🤖 Анализ AI",
        "btn_favorites": "❤️ Избранное",
        "fav_added": "⭐ Добавлено в избранное",
        "fav_removed": "Убрано из избранного",
        "no_favorites": "У вас пока нет избранных команд. Добавьте через меню матча — кнопка ⭐ рядом с названием команды.",
        "favorites_header": "Ваши избранные команды (уведомим за час до матча):",
        "fav_notify_header": "🔔 Через час матч вашей команды!",
        "btn_accuracy": "📈 Точность AI",
        "accuracy_none": "Пока нет ни одного завершённого матча с прогнозом AI. Загляните позже.",
        "accuracy_header": "📈 Точность прогнозов AI\n\nВерно: {correct} из {total}\nТочность: {pct}%",
        "btn_back": "⬅️ Назад",
        "btn_back_to_games": "⬅️ К списку игр",
        "no_games": "На ближайшие 24 часа матчей в выбранных лигах не найдено.",
        "loading_games": "Загружаю список матчей...",
        "loading_stats": "Собираю статистику по матчу...",
        "loading_ai": "🤖 Groq анализирует статистику, подождите...",
        "stats_unavailable": "Статистика по этому матчу пока недоступна.",
        "choose_game": "Матчи на ближайшие 24 часа:",
        "choose_league_filter": "Выберите лигу:",
        "btn_all_leagues": "Все",
        "no_games_league": "В этой лиге на ближайшие 24 часа матчей не найдено.",
        "game_menu": "Выберите, что показать по матчу:",
        "corners_note": "ℹ️ Некоторые метрики (например, попадания в штангу) доступны не для всех турниров бесплатного тарифа API.",
        "low_data_note": "  ⚠️ По этой команде мало статистики — выводы менее надёжны.",
        "form_header": "📊 Среднее за последние {n} матчей:",
        "form_no_data": "  нет данных по прошедшим матчам",
        "ai_disclaimer": "\n\n⚠️ Это не финансовый совет, а аналитика на основе статистики.",
        "error_api": "⚠️ Не удалось получить данные от источника статистики. Попробуйте позже.",
    },
    "en": {
        "choose_language": "Выберите язык / Choose your language:",
        "ask_password": "Enter the password to access the bot:",
        "wrong_password": "❌ Wrong password. Try again:",
        "access_granted": "✅ Access granted! Welcome.",
        "main_menu": "Main menu. Choose an action:",
        "btn_games": "⚽ Games (24h)",
        "btn_stats": "📊 Statistics",
        "btn_ai": "🤖 AI Analysis",
        "btn_favorites": "❤️ Favorites",
        "fav_added": "⭐ Added to favorites",
        "fav_removed": "Removed from favorites",
        "no_favorites": "You have no favorite teams yet. Add one from a match menu — the ⭐ button next to the team name.",
        "favorites_header": "Your favorite teams (you'll be notified an hour before kickoff):",
        "fav_notify_header": "🔔 Your team plays in an hour!",
        "btn_accuracy": "📈 AI accuracy",
        "accuracy_none": "No AI-predicted matches have finished yet. Check back later.",
        "accuracy_header": "📈 AI prediction accuracy\n\nCorrect: {correct} out of {total}\nAccuracy: {pct}%",
        "btn_back": "⬅️ Back",
        "btn_back_to_games": "⬅️ Back to games",
        "no_games": "No matches found in the next 24 hours for the tracked leagues.",
        "loading_games": "Loading matches...",
        "loading_stats": "Gathering match statistics...",
        "loading_ai": "🤖 Groq is analyzing the stats, please wait...",
        "stats_unavailable": "Statistics for this match are not available yet.",
        "choose_game": "Matches in the next 24 hours:",
        "choose_league_filter": "Choose a league:",
        "btn_all_leagues": "All",
        "no_games_league": "No matches found for this league in the next 24 hours.",
        "game_menu": "Choose what to show for this match:",
        "corners_note": "ℹ️ Some metrics (e.g. hitting the woodwork) aren't available for every competition on the free API plan.",
        "low_data_note": "  ⚠️ Limited data for this team — the analysis is less reliable.",
        "form_header": "📊 Average over the last {n} matches:",
        "form_no_data": "  no data from past matches",
        "ai_disclaimer": "\n\n⚠️ This is not financial advice, just stats-based analysis.",
        "error_api": "⚠️ Couldn't fetch data from the stats provider. Please try again later.",
    },
}


def t(lang: str, key: str) -> str:
    return TEXTS.get(lang, TEXTS["ru"]).get(key, key)


# Short labels for league-filter buttons (full names live in config.LEAGUES).
LEAGUE_SHORT = {
    "ru": {
        39: "АПЛ", 140: "Ла Лига", 135: "Серия А", 78: "Бундеслига", 61: "Лига 1",
        88: "Эредивизие", 94: "Примейра", 203: "Супер Лига", 235: "РПЛ",
        2: "ЛЧ", 3: "ЛЕ", 848: "ЛК",
    },
    "en": {
        39: "EPL", 140: "La Liga", 135: "Serie A", 78: "Bundesliga", 61: "Ligue 1",
        88: "Eredivisie", 94: "Primeira", 203: "Süper Lig", 235: "RPL",
        2: "UCL", 3: "UEL", 848: "UECL",
    },
}


def league_short(lang: str, league_id: int) -> str:
    return LEAGUE_SHORT.get(lang, LEAGUE_SHORT["ru"]).get(league_id, str(league_id))
