import datetime as dt
import aiohttp

from bot import config
from bot import database as db

HEADERS = {"x-apisports-key": config.API_FOOTBALL_KEY}


async def _get(session: aiohttp.ClientSession, path: str, params: dict) -> dict:
    url = f"{config.API_FOOTBALL_BASE}{path}"
    async with session.get(url, headers=HEADERS, params=params, timeout=20) as resp:
        resp.raise_for_status()
        return await resp.json()


async def get_fixtures_next_24h() -> list[dict]:
    """Fixtures in the next 24h, restricted to leagues in config.LEAGUES.
    Cached for FIXTURES_CACHE_TTL so we don't burn the free daily quota.
    """
    today = dt.datetime.utcnow().date()
    cache_key = f"fixtures:{today.isoformat()}"
    cached = await db.cache_get(cache_key)
    if cached is not None:
        return cached

    now = dt.datetime.utcnow()
    horizon = now + dt.timedelta(hours=24)
    dates = {today.isoformat(), (today + dt.timedelta(days=1)).isoformat()}

    fixtures: list[dict] = []
    async with aiohttp.ClientSession() as session:
        for date_str in dates:
            data = await _get(session, "/fixtures", {"date": date_str})
            for item in data.get("response", []):
                league_id = item["league"]["id"]
                if league_id not in config.LEAGUES:
                    continue
                ts = item["fixture"]["timestamp"]
                match_time = dt.datetime.utcfromtimestamp(ts)
                if not (now <= match_time <= horizon):
                    continue
                fixture = {
                    "id": item["fixture"]["id"],
                    "home": item["teams"]["home"]["name"],
                    "away": item["teams"]["away"]["name"],
                    "home_id": item["teams"]["home"]["id"],
                    "away_id": item["teams"]["away"]["id"],
                    "league_id": league_id,
                    "league_name": config.LEAGUES[league_id],
                    "season": item["league"]["season"],
                    "time": match_time.strftime("%d.%m %H:%M UTC"),
                    "timestamp": ts,
                }
                fixtures.append(fixture)
                await db.cache_set(
                    f"fixture_meta:{fixture['id']}", fixture, config.FIXTURES_CACHE_TTL
                )

    fixtures.sort(key=lambda f: f["timestamp"])
    await db.cache_set(cache_key, fixtures, config.FIXTURES_CACHE_TTL)
    return fixtures


async def get_fixture_meta(fixture_id: int) -> dict | None:
    return await db.cache_get(f"fixture_meta:{fixture_id}")


async def get_team_statistics(team_id: int, league_id: int, season: int) -> dict | None:
    cache_key = f"team_stats:{team_id}:{league_id}:{season}"
    cached = await db.cache_get(cache_key)
    if cached is not None:
        return cached

    async with aiohttp.ClientSession() as session:
        data = await _get(
            session,
            "/teams/statistics",
            {"team": team_id, "league": league_id, "season": season},
        )
    stats = data.get("response")
    if not stats:
        return None
    await db.cache_set(cache_key, stats, config.TEAM_STATS_CACHE_TTL)
    return stats


# Map API-Football's fixture-statistics "type" labels (case-insensitive) to
# short internal keys. If API-Football adds/renames a type, unknown types are
# simply skipped rather than guessed at.
_STAT_TYPE_MAP = {
    "corner kicks": "corners",
    "yellow cards": "yellow_cards",
    "red cards": "red_cards",
    "shots on goal": "shots_on_target",
    "total shots": "shots_total",
    "fouls": "fouls",
    "offsides": "offsides",
    "ball possession": "possession_pct",
    "hit woodwork": "woodwork",  # only included if/when the API actually sends it
}


async def get_last_finished_fixtures(team_id: int, n: int = None) -> list[int]:
    """IDs of a team's last N *finished* matches (any competition)."""
    n = n or config.LAST_N_MATCHES
    cache_key = f"last_fixtures:{team_id}:{n}"
    cached = await db.cache_get(cache_key)
    if cached is not None:
        return cached

    async with aiohttp.ClientSession() as session:
        # Ask for a few extra in case some recent ones aren't finished yet.
        data = await _get(session, "/fixtures", {"team": team_id, "last": n + 3})

    ids = []
    for item in data.get("response", []):
        if item["fixture"]["status"]["short"] in ("FT", "AET", "PEN"):
            ids.append(item["fixture"]["id"])
    ids = ids[-n:] if len(ids) > n else ids

    await db.cache_set(cache_key, ids, config.LAST_FIXTURES_CACHE_TTL)
    return ids


async def get_fixture_team_statistics(fixture_id: int, team_id: int) -> dict:
    """Raw per-match stats (corners, cards, shots...) for one team in one
    finished fixture. Cached long-term since historical data is immutable.
    """
    cache_key = f"fixture_stats:{fixture_id}:{team_id}"
    cached = await db.cache_get(cache_key)
    if cached is not None:
        return cached

    async with aiohttp.ClientSession() as session:
        data = await _get(
            session, "/fixtures/statistics", {"fixture": fixture_id, "team": team_id}
        )

    result: dict = {}
    response = data.get("response", [])
    if response:
        for stat in response[0].get("statistics", []):
            raw_type = (stat.get("type") or "").strip().lower()
            key = _STAT_TYPE_MAP.get(raw_type)
            if not key:
                continue
            value = stat.get("value")
            if isinstance(value, str) and value.endswith("%"):
                try:
                    value = int(value.rstrip("%"))
                except ValueError:
                    value = None
            if isinstance(value, (int, float)):
                result[key] = value

    await db.cache_set(cache_key, result, config.FIXTURE_STATS_CACHE_TTL)
    return result


async def get_last_n_form_summary(team_id: int, n: int = None) -> dict:
    """Average per-match stats (corners, cards, shots...) over a team's last
    N finished matches, computed from real match-by-match data.
    """
    n = n or config.LAST_N_MATCHES
    cache_key = f"form_summary:{team_id}:{n}"
    cached = await db.cache_get(cache_key)
    if cached is not None:
        return cached

    fixture_ids = await get_last_finished_fixtures(team_id, n)
    if not fixture_ids:
        return {"matches_analyzed": 0, "averages": {}}

    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for fid in fixture_ids:
        stats = await get_fixture_team_statistics(fid, team_id)
        for key, value in stats.items():
            totals[key] = totals.get(key, 0) + value
            counts[key] = counts.get(key, 0) + 1

    averages = {
        key: round(totals[key] / counts[key], 1) for key in totals if counts[key]
    }
    summary = {"matches_analyzed": len(fixture_ids), "averages": averages}
    await db.cache_set(cache_key, summary, config.LAST_FIXTURES_CACHE_TTL)
    return summary


async def get_fixture_result(fixture_id: int) -> dict | None:
    """Final outcome of a fixture once it's finished, else None (not started,
    in progress, or postponed). Not cached: called a handful of times per
    match by the prediction tracker, well within the free daily quota.
    """
    async with aiohttp.ClientSession() as session:
        data = await _get(session, "/fixtures", {"id": fixture_id})

    response = data.get("response", [])
    if not response:
        return None

    item = response[0]
    status = item["fixture"]["status"]["short"]
    if status not in ("FT", "AET", "PEN"):
        return None

    home_goals = item["goals"]["home"]
    away_goals = item["goals"]["away"]
    if home_goals is None or away_goals is None:
        return None

    if home_goals > away_goals:
        outcome = "home"
    elif away_goals > home_goals:
        outcome = "away"
    else:
        outcome = "draw"

    return {"home_goals": home_goals, "away_goals": away_goals, "outcome": outcome}


async def get_head_to_head(home_id: int, away_id: int, last: int = 5) -> list[dict]:
    cache_key = f"h2h:{home_id}:{away_id}:{last}"
    cached = await db.cache_get(cache_key)
    if cached is not None:
        return cached

    async with aiohttp.ClientSession() as session:
        data = await _get(
            session,
            "/fixtures/headtohead",
            {"h2h": f"{home_id}-{away_id}", "last": last},
        )
    results = data.get("response", [])
    summary = []
    for item in results:
        summary.append(
            {
                "date": item["fixture"]["date"][:10],
                "home": item["teams"]["home"]["name"],
                "away": item["teams"]["away"]["name"],
                "home_goals": item["goals"]["home"],
                "away_goals": item["goals"]["away"],
            }
        )
    await db.cache_set(cache_key, summary, config.H2H_CACHE_TTL)
    return summary
