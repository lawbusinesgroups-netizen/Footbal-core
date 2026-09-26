import asyncio
import datetime as dt
import logging

from aiogram import Bot

from bot import config
from bot import database as db
from bot.locales import t
from bot.services import api_football

logger = logging.getLogger(__name__)


async def _check_and_notify(bot: Bot) -> None:
    await db.cleanup_old_notifications()

    try:
        fixtures = await api_football.get_fixtures_next_24h()
    except Exception:
        logger.exception("notifier: failed to fetch fixtures")
        return

    if not fixtures:
        return

    now = dt.datetime.utcnow()
    poll_slack_minutes = config.NOTIFY_CHECK_INTERVAL_SECONDS / 60
    window_start = config.NOTIFY_LEAD_MINUTES - poll_slack_minutes

    # Imported lazily to avoid a circular import (stats -> api_football,
    # notifier -> stats).
    from bot.handlers.stats import build_stats_text

    for fx in fixtures:
        kickoff = dt.datetime.utcfromtimestamp(fx["timestamp"])
        minutes_until = (kickoff - now).total_seconds() / 60
        if not (window_start <= minutes_until <= config.NOTIFY_LEAD_MINUTES):
            continue

        watchers = await db.get_watchers_for_teams([fx["home_id"], fx["away_id"]])
        user_ids = {user_id for user_id, _ in watchers}
        if not user_ids:
            continue

        for user_id in user_ids:
            if await db.was_notified(user_id, fx["id"]):
                continue

            lang = await db.get_language(user_id)
            try:
                text = await build_stats_text(lang, fx["id"])
            except Exception:
                logger.exception("notifier: failed to build stats for fixture %s", fx["id"])
                text = None

            if text:
                message = f"{t(lang, 'fav_notify_header')}\n\n{text}"
                try:
                    await bot.send_message(user_id, message, parse_mode="Markdown")
                except Exception:
                    logger.exception("notifier: failed to send to user %s", user_id)

            # Mark as notified even on failure, so a permanently blocked bot
            # or one bad fixture doesn't get retried forever every 5 minutes.
            await db.mark_notified(user_id, fx["id"])


async def run_scheduler(bot: Bot) -> None:
    """Runs forever: checks every NOTIFY_CHECK_INTERVAL_SECONDS for favorite
    matches about to start and sends a stats card to whoever favorited them.
    """
    while True:
        try:
            await _check_and_notify(bot)
        except Exception:
            logger.exception("notifier: unexpected error in scheduled check")
        await asyncio.sleep(config.NOTIFY_CHECK_INTERVAL_SECONDS)
