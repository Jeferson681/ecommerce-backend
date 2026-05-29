"""Script to delete expired idempotency keys.

Run manually or via cron: `python scripts/cleanup_idempotency.py`.

This script creates a short-lived Session, invokes the repository method
`delete_expired`, and commits the transaction. The repository itself does
not manage commits.
"""

from datetime import UTC, datetime

from backend.app.core.database import SessionLocal
from backend.app.idempotency.repositories.idempotency_repository import (
    IdempotencyRepository,
)


def main():
    now = datetime.now(UTC)

    session = SessionLocal()
    try:
        repo = IdempotencyRepository(session)
        # begin a transaction to ensure atomic delete
        with session.begin():
            deleted = repo.delete_expired(now)
        print(f"Deleted {deleted} expired idempotency keys")
    finally:
        session.close()


if __name__ == "__main__":
    main()
