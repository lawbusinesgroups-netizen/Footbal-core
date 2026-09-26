import asyncio
import datetime as dt
import logging

from bot import config
from bot.services import api_football

logger = logging.getLogger(__name__)


async def warm_cache_once() -> None:
    """Pre-fetch stats for the soonest N matches of the day, so the first
    real user of the day doesn't pay the API-quota cost alone.
    """
    try:
        fixtures = await api_football.get_fixtures_next_24h()
    except Exception:
        logger.exception("cache warm: failed to fetch fixtures")
        return

    if not fixtures:
        logger.info("cache warm: no fixtures today, nothing to warm")
        return

    # fixtures is already sorted by kickoff time; take the soonest N to stay
    # inside the free daily quota.
    targets = fixtures[: config.CACHE_WARM_LIMIT]

    # Imported lazily to avoid a circular import (stats -> api_football,
    # cache_warmer -> stats).
    from bot.handlers.stats import build_stats_text

    warmed = 0
    for fx in targets:
        try:
            await build_stats_text("ru", fx["id"])
            warmed += 1
        except Exception:
            logger.exception("cache warm: failed for fixture %s", fx["id"])

    logger.info("cache warm: warmed %d/%d fixtures", warmed, len(targets))


async def _seconds_until_next_run() -> float:
    now = dt.datetime.utcnow()
    target = now.replace(
        hour=config.CACHE_WARM_HOUR_UTC, minute=0, second=0, microsecond=0
    )
    if target <= now:
        target += dt.timedelta(days=1)
    return (target - now).total_seconds()


async def run_scheduler() -> None:
    """Runs forever: warms the cache once a day at config.CACHE_WARM_HOUR_UTC.
    Meant to be launched as a background asyncio task alongside polling.
    """
    while True:
        delay = await _seconds_until_next_run()
        logger.info("cache warm: next run in %.0f minutes", delay / 60)
        await asyncio.sleep(delay)
        try:
            await warm_cache_once()
        except Exception:
            logger.exception("cache warm: unexpected error in scheduled run")
