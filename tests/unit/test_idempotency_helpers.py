import os
import sys

# Ensure project root is on sys.path for test collection environments
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


import pytest  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from backend.app.core.database import Base, SessionLocal, engine  # noqa: E402
from backend.app.core.exceptions import ValidationError  # noqa: E402
from backend.app.idempotency.helpers import (  # noqa: E402
    persist_idempotency_response,
    reserve_idempotency_key,
    try_replay,
)
from backend.app.idempotency.repository import IdempotencyKeyRepository  # noqa: E402


class DummyModel(BaseModel):
    x: int


def setup_module(module: object) -> None:
    # ensure related ORM models are imported so their tables are registered
    import backend.app.modules.user.domain.models as _user_models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def test_try_replay_none_when_missing() -> None:
    session = SessionLocal()
    repo = IdempotencyKeyRepository(session)

    assert try_replay(repo, "no-key", DummyModel) is None
    session.close()


def test_reserve_and_persist_cycle() -> None:
    session = SessionLocal()
    repo = IdempotencyKeyRepository(session)

    key = "helper-key-1"
    record, created = reserve_idempotency_key(repo, key, user_id=9, request_hash="h9")
    assert created is True

    # second reservation should raise because it's in progress
    with pytest.raises(ValidationError):
        reserve_idempotency_key(repo, key, user_id=9, request_hash="h9")

    # persist response and then replay should return model
    persist_idempotency_response(repo, key, user_id=9, status=201, body='{"x": 5}')

    replay = try_replay(repo, key, DummyModel)
    assert replay is not None
    assert replay.x == 5
    session.close()
