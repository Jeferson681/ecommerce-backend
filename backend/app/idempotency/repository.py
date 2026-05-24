"""Idempotency repository for handling idempotent requests."""

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.idempotency.models import IdempotencyKey


class IdempotencyKeyRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_key(self, key: str) -> IdempotencyKey | None:
        statement = select(IdempotencyKey).where(IdempotencyKey.key == key)

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

    def get_or_create(
        self,
        idempotency_key: IdempotencyKey,
    ) -> tuple[IdempotencyKey, bool]:
        """Try to create the idempotency key record. Returns (record, created).

        This handles race conditions by catching IntegrityError on flush and
        returning the existing record when another transaction inserted first.
        """
        try:
            self.session.add(idempotency_key)
            self.session.flush()
            self.session.refresh(idempotency_key)
            return idempotency_key, True
        except IntegrityError:
            # Another transaction likely created the same key concurrently.
            self.session.rollback()
            existing = self.get_by_key(idempotency_key.key)
            if existing is None:
                # Unexpected: re-raise to surface the original issue
                raise
            return existing, False

    def save_response(self, key: str, user_id: int, status: int, body: str) -> None:
        statement = (
            update(IdempotencyKey)
            .where(IdempotencyKey.key == key, IdempotencyKey.user_id == user_id)
            .values(response_status=status, response_body=body)
        )

        self.session.execute(statement)
        self.session.flush()

    def create(
        self,
        idempotency_key: IdempotencyKey,
    ) -> IdempotencyKey:
        self.session.add(idempotency_key)
        self.session.flush()
        self.session.refresh(idempotency_key)

        return idempotency_key
