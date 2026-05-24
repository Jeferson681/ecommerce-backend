from typing import Any, TypeVar, cast

from backend.app.core.exceptions import ValidationError
from backend.app.idempotency.repository import IdempotencyKeyRepository
from backend.app.idempotency.service import create_idempotency_record

T = TypeVar("T")


def try_replay(
    repository: IdempotencyKeyRepository, key: str, model_cls: type[Any]
) -> T | None:
    """Return deserialized model if an idempotent response exists, else None."""
    record = repository.get_by_key(key)
    if record is None:
        return None
    if record.response_status is None:
        return None
    if record.response_body is None:
        raise ValidationError("Idempotency record has no stored response.")
    result = model_cls.model_validate_json(record.response_body)
    return cast(T, result)


def reserve_idempotency_key(
    repository: IdempotencyKeyRepository, key: str, user_id: int, request_hash: str
) -> tuple[Any, bool]:
    """Try to create or reserve an idempotency key. Returns (record, created).

    Raises ValidationError if another in-progress request holds the key.
    """
    # quick-path: if an existing record is visible in this session, return it
    existing = repository.get_by_key(key)
    if existing is not None:
        if existing.response_status is not None:
            if existing.response_body is None:
                raise ValidationError("Idempotency record has no stored response.")
            return existing, False
        raise ValidationError("Idempotent request already in progress.")

    new_record = create_idempotency_record(
        key=key, user_id=user_id, request_hash=request_hash
    )
    record, created = repository.get_or_create(new_record)
    if not created:
        if record.response_status is not None:
            if record.response_body is None:
                raise ValidationError("Idempotency record has no stored response.")
            return record, False
        raise ValidationError("Idempotent request already in progress.")
    return record, True


def persist_idempotency_response(
    repository: IdempotencyKeyRepository, key: str, user_id: int, status: int, body: str
) -> None:
    repository.save_response(key, user_id, status, body)
