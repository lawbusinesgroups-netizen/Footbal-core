import asyncio
import datetime as dt
import logging

from bot import database as db
from bot.services import api_football

logger = logging.getLogger(__name__)

# Wait this long after kickoff before checking a result, so the match has
# had time to finish (regular + stoppage + extra time/penalties, worst case).
RESOLVE_DELAY_SECONDS = 60 * 60 * 3  # 3 hours

CHECK_INTERVAL_SECONDS = 60 * 30  # 30 minutes


async def _resolve_pending() -> None:
    cutoff = dt.datetime.utcnow().timestamp() - RESOLVE_DELAY_SECONDS
    pending = await db.get_unresolved_predictions(cutoff)
    if not pending:
        return

    for pred in pending:
        try:
            result = await api_football.get_fixture_result(pred["fixture_id"])
        except Exception:
            logger.exception(
                "prediction tracker: failed to fetch result for fixture %s",
                pred["fixture_id"],
            )
            continue

        if not result:
            # Not finished yet (postponed, rescheduled, still delayed) —
            # leave unresolved and retry on the next cycle.
            continue

        correct = pred["pick"] == result["outcome"]
        await db.resolve_prediction(pred["fixture_id"], result["outcome"], correct)


async def run_scheduler() -> None:
    """Runs forever: every CHECK_INTERVAL_SECONDS, resolves predictions for
    matches that should be finished by now against the real result."""
    while True:
        try:
            await _resolve_pending()
        except Exception:
            logger.exception("prediction tracker: unexpected error")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
