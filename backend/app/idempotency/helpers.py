import json
from typing import Any

from backend.app.core.exceptions import ValidationError
from backend.app.idempotency.domain.models import IdempotencyKey
from backend.app.idempotency.repositories import IdempotencyRepository
from backend.app.idempotency.service import (
    create_idempotency_record,
    validate_idempotency_key,
)

NO_STORED_RESPONSE_ERROR = "Idempotency record has no stored response."
JSONData = dict[str, Any] | list[Any]


def try_replay(
    repository: IdempotencyRepository,
    idempotency_key: str,
    user_id: int | None = None,
) -> JSONData | None:
    """Return deserialized payload (mapping) if an idempotent response exists, else None.

    Note: This function deliberately returns raw Python structures (dict/list)
    and does NOT perform Pydantic model validation to avoid double-validation.
    Callers should validate using the appropriate schema once.
    """
    record = repository.get_by_key(idempotency_key, user_id)
    if record is None:
        return None
    if record.response_status is None:
        return None
    if record.response_body is None:
        raise ValidationError(NO_STORED_RESPONSE_ERROR)

    body = record.response_body

    payload = json.loads(body)

    if not isinstance(payload, dict | list):
        raise ValidationError(
            "Stored idempotency response is not a JSON object or array."
        )

    return payload


def reserve_idempotency_key(
    repository: IdempotencyRepository,
    idempotency_key: str,
    user_id: int,
    request_hash: str,
) -> tuple[IdempotencyKey, bool]:
    """Try to create or reserve an idempotency key. Returns (record, created).

    Raises ValidationError if another in-progress request holds the key.
    """
    # quick-path: if an existing record is visible in this session, return it
    existing = repository.get_by_key(idempotency_key, user_id)
    validated = validate_idempotency_key(existing, user_id, request_hash)
    if validated is not None:
        if validated.response_status is not None:
            if validated.response_body is None:
                raise ValidationError(NO_STORED_RESPONSE_ERROR)
            return validated, False
        raise ValidationError("Idempotent request already in progress.")

    new_record = create_idempotency_record(idempotency_key, user_id, request_hash)

    # Attempt to claim the key using the repository (nested transaction).
    record, created = repository.claim(new_record)

    if not created:
        validated = validate_idempotency_key(record, user_id, request_hash)
        if validated is None:
            raise ValidationError("Failed to reserve idempotency key.")
        if validated.response_status is not None:
            if validated.response_body is None:
                raise ValidationError(NO_STORED_RESPONSE_ERROR)
            return validated, False
        raise ValidationError("Idempotent request already in progress.")

    return record, True


def persist_idempotency_response(
    repository: IdempotencyRepository,
    idempotency_key: str,
    user_id: int,
    status: int,
    body: str,
) -> None:
    repository.save_response(idempotency_key, user_id, status, body)


def validate_idempotency_input(
    idempotency_key: str | None,
    request_hash: str | None,
) -> None:
    if bool(idempotency_key) != bool(request_hash):
        raise ValidationError(
            "Both idempotency_key and request_hash must be provided together."
        )


def reserve_idempotency_if_needed(
    repository: IdempotencyRepository,
    idempotency_key: str | None,
    request_hash: str | None,
    user_id: int,
) -> None:
    if idempotency_key is None or request_hash is None:
        return

    reserve_idempotency_key(
        repository=repository,
        idempotency_key=idempotency_key,
        user_id=user_id,
        request_hash=request_hash,
    )
