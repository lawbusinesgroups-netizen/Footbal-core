import json
import time
import aiosqlite

from bot.config import DB_PATH, DEFAULT_LANGUAGE

_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    language TEXT NOT NULL DEFAULT 'ru',
    authenticated INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
)
"""

_CREATE_CACHE = """
CREATE TABLE IF NOT EXISTS api_cache (
    cache_key TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    expires_at REAL NOT NULL
)
"""

_CREATE_FAVORITES = """
CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (user_id, team_id)
)
"""

# Tracks which (user, fixture) "1 hour before kickoff" notifications have
# already been sent, so a restart or a slow poll cycle never double-sends.
_CREATE_NOTIFIED = """
CREATE TABLE IF NOT EXISTS notified_fixtures (
    user_id INTEGER NOT NULL,
    fixture_id INTEGER NOT NULL,
    notified_at REAL NOT NULL,
    PRIMARY KEY (user_id, fixture_id)
)
"""

# One row per fixture: the AI's match-winner pick, and (once the match is
# over) whether it was correct. Powers the accuracy tracking.
_CREATE_PREDICTIONS = """
CREATE TABLE IF NOT EXISTS predictions (
    fixture_id INTEGER PRIMARY KEY,
    home_name TEXT NOT NULL,
    away_name TEXT NOT NULL,
    pick TEXT NOT NULL,
    kickoff_ts INTEGER NOT NULL,
    created_at REAL NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0,
    correct INTEGER,
    actual_result TEXT,
    resolved_at REAL
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_USERS)
        await db.execute(_CREATE_CACHE)
        await db.execute(_CREATE_FAVORITES)
        await db.execute(_CREATE_NOTIFIED)
        await db.execute(_CREATE_PREDICTIONS)
        await db.commit()


async def ensure_user(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, language, authenticated, created_at) "
            "VALUES (?, ?, 0, ?)",
            (user_id, DEFAULT_LANGUAGE, time.time()),
        )
        await db.commit()


async def set_language(user_id: int, language: str) -> None:
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE user_id = ?", (language, user_id)
        )
        await db.commit()


async def get_language(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else DEFAULT_LANGUAGE


async def set_authenticated(user_id: int, value: bool) -> None:
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET authenticated = ? WHERE user_id = ?",
            (1 if value else 0, user_id),
        )
        await db.commit()


async def is_authenticated(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT authenticated FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return bool(row and row[0])


async def cache_get(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT data, expires_at FROM api_cache WHERE cache_key = ?", (key,)
        )
        row = await cur.fetchone()
        if not row:
            return None
        data, expires_at = row
        if expires_at < time.time():
            return None
        return json.loads(data)


async def cache_set(key: str, value, ttl_seconds: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO api_cache (cache_key, data, expires_at) VALUES (?, ?, ?) "
            "ON CONFLICT(cache_key) DO UPDATE SET data = excluded.data, "
            "expires_at = excluded.expires_at",
            (key, json.dumps(value), time.time() + ttl_seconds),
        )
        await db.commit()


async def add_favorite(user_id: int, team_id: int, team_name: str) -> None:
    await ensure_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, team_id, team_name, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, team_id, team_name, time.time()),
        )
        await db.commit()


async def remove_favorite(user_id: int, team_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM favorites WHERE user_id = ? AND team_id = ?", (user_id, team_id)
        )
        await db.commit()


async def is_favorite(user_id: int, team_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND team_id = ?", (user_id, team_id)
        )
        return (await cur.fetchone()) is not None


async def list_favorites(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT team_id, team_name FROM favorites WHERE user_id = ? ORDER BY team_name",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [{"team_id": r[0], "team_name": r[1]} for r in rows]


async def get_watchers_for_teams(team_ids: list[int]) -> list[tuple[int, int]]:
    """(user_id, team_id) pairs for every user who favorited one of these teams."""
    if not team_ids:
        return []
    placeholders = ",".join("?" for _ in team_ids)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            f"SELECT user_id, team_id FROM favorites WHERE team_id IN ({placeholders})",
            team_ids,
        )
        return await cur.fetchall()


async def was_notified(user_id: int, fixture_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM notified_fixtures WHERE user_id = ? AND fixture_id = ?",
            (user_id, fixture_id),
        )
        return (await cur.fetchone()) is not None


async def mark_notified(user_id: int, fixture_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO notified_fixtures (user_id, fixture_id, notified_at) "
            "VALUES (?, ?, ?)",
            (user_id, fixture_id, time.time()),
        )
        await db.commit()


async def cleanup_old_notifications(max_age_seconds: int = 60 * 60 * 24 * 2) -> None:
    cutoff = time.time() - max_age_seconds
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM notified_fixtures WHERE notified_at < ?", (cutoff,))
        await db.commit()


async def save_prediction(
    fixture_id: int, home_name: str, away_name: str, pick: str, kickoff_ts: int
) -> None:
    """One row per fixture — repeat AI-analysis requests for the same match
    don't overwrite the original tracked prediction."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO predictions "
            "(fixture_id, home_name, away_name, pick, kickoff_ts, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (fixture_id, home_name, away_name, pick, kickoff_ts, time.time()),
        )
        await db.commit()


async def get_unresolved_predictions(kickoff_before_ts: float) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT fixture_id, pick FROM predictions "
            "WHERE resolved = 0 AND kickoff_ts < ?",
            (kickoff_before_ts,),
        )
        rows = await cur.fetchall()
        return [{"fixture_id": r[0], "pick": r[1]} for r in rows]


async def resolve_prediction(fixture_id: int, actual_result: str, correct: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE predictions SET resolved = 1, correct = ?, actual_result = ?, "
            "resolved_at = ? WHERE fixture_id = ?",
            (1 if correct else 0, actual_result, time.time(), fixture_id),
        )
        await db.commit()


async def get_accuracy_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*), COALESCE(SUM(correct), 0) FROM predictions WHERE resolved = 1"
        )
        total, correct = await cur.fetchone()
        pct = round(100 * correct / total, 1) if total else None
        return {"total": total, "correct": correct, "accuracy_pct": pct}
