"""Idempotency service: pure business helpers (no DB/session ops)."""

from datetime import UTC, datetime, timedelta

from backend.app.core.exceptions import ValidationError
from backend.app.idempotency.domain.models import IdempotencyKey

# Default TTL for idempotency keys (hours)
DEFAULT_EXPIRATION_HOURS = 24


def validate_idempotency_key(
    existing_key: IdempotencyKey | None,
    user_id: int,
    request_hash: str,
) -> IdempotencyKey | None:
    """Validate whether an existing idempotency key can be reused.

    Returns the `existing_key` when validation passes, or `None` when no
    existing key is present. Raises `ValidationError` on ownership/hash
    mismatches.
    """
    if existing_key is None:
        return None

    if existing_key.user_id != user_id:
        raise ValidationError("Idempotency key does not belong to this user.")

    if existing_key.request_hash != request_hash:
        raise ValidationError("Idempotency key was already used for another request.")

    return existing_key


def create_idempotency_record(
    key: str, user_id: int, request_hash: str
) -> IdempotencyKey:
    """Build a new `IdempotencyKey` instance (no DB operations).

    The caller (helpers/use_cases) is responsible for persisting via the
    repository and managing transactions.
    """
    return IdempotencyKey(
        key=key,
        user_id=user_id,
        request_hash=request_hash,
        response_status=None,
        response_body=None,
        expires_at=datetime.now(UTC) + timedelta(hours=DEFAULT_EXPIRATION_HOURS),
    )
