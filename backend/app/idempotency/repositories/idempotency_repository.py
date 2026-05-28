"""Idempotency repository for handling idempotent requests."""

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.idempotency.domain.models import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_key(
        self,
        key: str,
        user_id: int | None = None,
    ) -> IdempotencyKey | None:
        statement = select(IdempotencyKey).where(IdempotencyKey.key == key)

        if user_id is not None:
            statement = statement.where(IdempotencyKey.user_id == user_id)

        result = self.session.execute(statement)

        return result.scalar_one_or_none()

    def get_by_request_hash(
        self,
        request_hash: str,
    ) -> IdempotencyKey | None:
        statement = select(IdempotencyKey).where(
            IdempotencyKey.request_hash == request_hash
        )

        result = self.session.execute(statement)

        return result.scalar_one_or_none()

    def claim(
        self,
        idempotency_key: IdempotencyKey,
    ) -> tuple[IdempotencyKey, bool]:
        """Attempt to reserve an idempotency key using the repository
        session. The repository does not manage transactions beyond using a
        nested transaction to detect constraint violations.

        Returns (record, created).
        """

        try:
            with self.session.begin_nested():
                self.session.add(idempotency_key)
                self.session.flush()

            return idempotency_key, True

        except IntegrityError:
            existing = self.get_by_key(idempotency_key.key, idempotency_key.user_id)
            if existing is None:
                raise
            return existing, False

    def save_response(
        self,
        key: str,
        user_id: int,
        status: int,
        body: str,
    ) -> bool:
        statement = (
            update(IdempotencyKey)
            .where(
                IdempotencyKey.key == key,
                IdempotencyKey.user_id == user_id,
                IdempotencyKey.response_status.is_(None),
            )
            .values(
                response_status=status,
                response_body=body,
            )
        )

        result = self.session.execute(statement)

        self.session.flush()

        return int(getattr(result, "rowcount", 0) or 0) > 0

    def delete_by_key(
        self,
        key: str,
        user_id: int,
    ) -> bool:
        statement = delete(IdempotencyKey).where(
            IdempotencyKey.key == key,
            IdempotencyKey.user_id == user_id,
        )

        result = self.session.execute(statement)
        self.session.flush()

        return int(getattr(result, "rowcount", 0) or 0) > 0

    def delete_expired(self, before: datetime) -> int:
        """Delete idempotency records with `expires_at` earlier than `before`.

        Returns the number of rows deleted. The repository does not commit;
        the caller is responsible for transaction lifecycle.
        """
        stmt = delete(IdempotencyKey).where(IdempotencyKey.expires_at < before)

        result = self.session.execute(stmt)

        # ensure DB changes are flushed to the transaction
        self.session.flush()

        return int(getattr(result, "rowcount", 0) or 0)
