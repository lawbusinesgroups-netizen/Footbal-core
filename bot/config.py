import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
SPORTSDB_KEY = os.getenv("SPORTSDB_KEY", "3")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD", "Xaru2004")

DB_PATH = os.getenv("DB_PATH", "bot_data.sqlite3")

# API-Football hosts a direct (non-RapidAPI) API. Free plan = 100 req/day.
API_FOOTBALL_BASE = "https://v3.football.api-sports.io"

# TheSportsDB free API (no hard daily limit on the free test key).
SPORTSDB_BASE = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_KEY}"

# How long cached fixtures / team stats stay valid, in seconds.
FIXTURES_CACHE_TTL = 60 * 60 * 2       # 2 hours
TEAM_STATS_CACHE_TTL = 60 * 60 * 12    # 12 hours
H2H_CACHE_TTL = 60 * 60 * 24           # 24 hours

# Last-N-matches form: the list of "which matches were the last 5" changes
# only once a team plays again, so a shortish TTL is fine.
LAST_FIXTURES_CACHE_TTL = 60 * 60 * 6  # 6 hours
# Per-match statistics for a FINISHED game never change, so cache them for a
# long time (effectively "forever" within the free daily quota's lifetime).
FIXTURE_STATS_CACHE_TTL = 60 * 60 * 24 * 30  # 30 days

LAST_N_MATCHES = 5

# Below this many analyzed matches (out of LAST_N_MATCHES) in the form
# summary, we warn the user that the data is thin rather than staying silent.
MIN_RELIABLE_MATCHES = int(os.getenv("MIN_RELIABLE_MATCHES", "3"))

# Whitelist of "top" leagues to show, mapped to API-Football league IDs.
# season is set to the current European season start year; API-Football
# expects e.g. 2025 for the 2025/2026 season for most European leagues.
CURRENT_SEASON = int(os.getenv("SEASON", "2025"))

LEAGUES = {
    # --- Европа: топ-дивизионы (без вторых лиг, без женских) ---
    39: "Premier League (England)",
    140: "La Liga (Spain)",
    135: "Serie A (Italy)",
    78: "Bundesliga (Germany)",
    61: "Ligue 1 (France)",
    88: "Eredivisie (Netherlands)",
    94: "Primeira Liga (Portugal)",
    203: "Süper Lig (Turkey)",
    235: "Premier League (Russia)",
    144: "Jupiler Pro League (Belgium)",
    179: "Premiership (Scotland)",
    106: "Ekstraklasa (Poland)",
    113: "Allsvenskan (Sweden)",
    103: "Eliteserien (Norway)",
    119: "Superliga (Denmark)",
    218: "Bundesliga (Austria)",
    207: "Super League (Switzerland)",
    197: "Super League 1 (Greece)",
    333: "Premier League (Ukraine)",
    71: "Serie A (Brazil)",
    253: "MLS (USA)",
    262: "Liga MX (Mexico)",
    98: "J1 League (Japan)",

    # --- Континентальные и международные турниры ---
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    848: "UEFA Europa Conference League",
    5: "UEFA Nations League",
    1: "World Cup",
    4: "Euro Championship",
    9: "Copa America",
    13: "CONMEBOL Libertadores",
    11: "CONMEBOL Sudamericana",
    6: "Africa Cup of Nations",
}

# ВАЖНО: этот список — базовый набор, в котором я уверен на 100%. Полного
# каталога лиг всех стран мира у меня нет возможности сверить "вживую" с
# API-Football, поэтому кто-то из менее популярных топ-дивизионов (Аргентина,
# Чили, Южная Корея, Саудовская Аравия, Хорватия, Сербия, Чехия и т.д.) в
# списке пока нет — рискованно вписывать ID наугад, можно случайно подставить
# не ту лигу. Чтобы дополнить список безопасно:
#   1. Возьми свой API_FOOTBALL_KEY
#   2. Запусти bot/tools/list_leagues.py (см. рядом) — он выгрузит ПОЛНЫЙ
#      официальный список лиг (без Cup, без Women) с их реальными ID
#   3. Из полученного списка добавь сюда нужные топ-дивизионы вручную

DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = ("ru", "en")

# Nightly cache-warm job: pre-fetch stats for the soonest N matches of the day
# so users hit a warm cache instead of the first click "paying" for everyone.
# Hour is in UTC; Tashkent is UTC+5, so 22 UTC == 03:00 Tashkent.
CACHE_WARM_HOUR_UTC = int(os.getenv("CACHE_WARM_HOUR_UTC", "22"))
# Cap to respect the free 100 req/day API-Football quota (each match costs a
# handful of requests the first time; repeats are free thanks to caching).
CACHE_WARM_LIMIT = int(os.getenv("CACHE_WARM_LIMIT", "8"))

# Favorites: notify a user this many minutes before kickoff, polling this
# often. The poll interval must be smaller than the lead time or a match
# can slip through the window between two checks.
NOTIFY_LEAD_MINUTES = int(os.getenv("NOTIFY_LEAD_MINUTES", "60"))
NOTIFY_CHECK_INTERVAL_SECONDS = int(os.getenv("NOTIFY_CHECK_INTERVAL_SECONDS", "300"))
