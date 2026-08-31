"""Periodic background runner for the temporary-data cleanup."""

import asyncio
import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from backend.app.application.use_cases.maintenance.cleanup import (
    run_temporary_data_cleanup_now,
)

logger = logging.getLogger(__name__)


async def cleanup_scheduler_loop(
    session_factory: Callable[[], Session],
    interval_seconds: float,
    stop_event: asyncio.Event,
) -> None:
    """Run the cleanup once at startup and then every `interval_seconds`.

    Exits as soon as `stop_event` is set. Database work is dispatched to a
    worker thread so the synchronous SQLAlchemy session never blocks the
    event loop. A failed cycle is logged and retried on the next interval —
    the application must never crash because of maintenance.
    """
    while not stop_event.is_set():
        try:
            result = await asyncio.to_thread(
                run_temporary_data_cleanup_now,
                session_factory,
            )
            logger.info("Scheduled temporary-data cleanup finished: %s", result)
        except Exception:
            logger.exception("Scheduled temporary-data cleanup failed")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except TimeoutError:
            continue
