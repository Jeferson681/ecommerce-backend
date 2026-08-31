"""Temporary-data maintenance use case.

Cross-domain workflow: coordinates the idempotency module and the auth
module (refresh tokens), so it belongs to the Application layer.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.idempotency.repositories.idempotency_repository import (
    IdempotencyRepository,
)
from backend.app.modules.auth.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from backend.app.uow.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


def run_temporary_data_cleanup(
    uow: UnitOfWork,
    now: datetime | None = None,
) -> dict[str, int]:
    """Delete expired idempotency records and expired/revoked refresh tokens.

    Both deletions run inside the transaction owned by the caller's UoW; the
    use case commits on success and rolls back before re-raising on failure.
    """
    moment = now or datetime.now(UTC)

    idempotency_repository = IdempotencyRepository(uow.session)
    refresh_token_repository = RefreshTokenRepository(uow.session)

    try:
        idempotency_deleted = idempotency_repository.delete_expired(moment)
        refresh_tokens_deleted = refresh_token_repository.delete_expired_or_revoked(
            moment
        )
        uow.commit()
    except Exception:
        uow.rollback()
        raise

    result = {
        "idempotency_keys": idempotency_deleted,
        "refresh_tokens": refresh_tokens_deleted,
    }
    logger.info("Temporary-data cleanup removed: %s", result)

    return result


def run_temporary_data_cleanup_now(
    session_factory: Callable[[], Session] = SessionLocal,
) -> dict[str, int]:
    """Run one cleanup cycle with its own session and UnitOfWork.

    Convenience entry point for the background scheduler and the manual
    script: it owns the session lifecycle (the UoW never closes sessions).
    """
    session = session_factory()
    try:
        with UnitOfWork(lambda: session) as uow:
            return run_temporary_data_cleanup(uow)
    finally:
        session.close()
