import aiohttp
from bot import config
from bot import database as db


async def _get(session: aiohttp.ClientSession, path: str, params: dict | None = None) -> dict:
    url = f"{config.SPORTSDB_BASE}{path}"
    async with session.get(url, params=params or {}, timeout=20) as resp:
        resp.raise_for_status()
        return await resp.json()


async def find_team_id(team_name: str) -> str | None:
    cache_key = f"sdb_team_id:{team_name.lower()}"
    cached = await db.cache_get(cache_key)
    if cached is not None:
        return cached or None

    async with aiohttp.ClientSession() as session:
        data = await _get(session, "/searchteams.php", {"t": team_name})
    teams = data.get("teams") or []
    team_id = teams[0]["idTeam"] if teams else None
    await db.cache_set(cache_key, team_id, config.TEAM_STATS_CACHE_TTL)
    return team_id


async def get_recent_form(team_name: str, last: int = 5) -> list[dict]:
    """Fallback/supplementary source: last results for a team by name.
    Used when API-Football quota is exhausted or as a cross-check.
    """
    cache_key = f"sdb_form:{team_name.lower()}:{last}"
    cached = await db.cache_get(cache_key)
    if cached is not None:
        return cached

    team_id = await find_team_id(team_name)
    if not team_id:
        return []

    async with aiohttp.ClientSession() as session:
        data = await _get(session, "/eventslast.php", {"id": team_id})
    events = (data.get("results") or [])[:last]
    form = []
    for ev in events:
        form.append(
            {
                "date": ev.get("dateEvent"),
                "home": ev.get("strHomeTeam"),
                "away": ev.get("strAwayTeam"),
                "home_score": ev.get("intHomeScore"),
                "away_score": ev.get("intAwayScore"),
            }
        )
    await db.cache_set(cache_key, form, config.TEAM_STATS_CACHE_TTL)
    return form
