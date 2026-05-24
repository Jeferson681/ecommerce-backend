"""Idempotency service for handling idempotent requests."""

from datetime import UTC, datetime, timedelta

from backend.app.core.exceptions import ValidationError
from backend.app.idempotency.models import IdempotencyKey
from backend.app.idempotency.repository import IdempotencyKeyRepository

DEFAULT_EXPIRATION_HOURS = 24


def create_idempotency_record(
    key: str,
    user_id: int,
    request_hash: str,
) -> IdempotencyKey:
    """Create a new idempotency record."""

    return IdempotencyKey(
        key=key,
        user_id=user_id,
        request_hash=request_hash,
        response_status=None,
        response_body=None,
        expires_at=datetime.now(UTC) + timedelta(hours=DEFAULT_EXPIRATION_HOURS),
    )


def validate_idempotency_key(
    key: str,
    user_id: int,
    request_hash: str,
    repository: IdempotencyKeyRepository,
) -> IdempotencyKey | None:
    """Validate whether an idempotency key can be reused."""

    existing_key = repository.get_by_key(key)

    if existing_key is None:
        return None

    if existing_key.user_id != user_id:
        raise ValidationError("Idempotency key does not belong to this user.")

    if existing_key.request_hash != request_hash:
        raise ValidationError("Idempotency key was already used for another request.")

    return existing_key
