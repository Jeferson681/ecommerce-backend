"""Integration tests for the temporary-data maintenance slice.

Covers the audited gap: expired idempotency records and expired/revoked
refresh tokens are removed, while valid records are preserved.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.application.use_cases.maintenance import scheduler as scheduler_module
from backend.app.application.use_cases.maintenance.cleanup import (
    run_temporary_data_cleanup,
    run_temporary_data_cleanup_now,
)
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.idempotency.domain.models import IdempotencyKey
from backend.app.main import app
from backend.app.modules.auth.domain.models import RefreshToken
from backend.app.modules.user.domain.models import User
from backend.app.uow.unit_of_work import UnitOfWork

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def _create_user(session, email: str) -> User:
    user = User(
        first_name="Maintenance",
        last_name="Test",
        email=email,
        password_hash="x",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _add_idempotency_key(session, user_id: int, key: str, expires_at) -> None:
    session.add(
        IdempotencyKey(
            key=key,
            user_id=user_id,
            request_hash=f"hash-{key}",
            expires_at=expires_at,
        )
    )


def _add_refresh_token(
    session,
    user_id: int,
    jti: str,
    expires_at,
    revoked: bool = False,
) -> None:
    session.add(
        RefreshToken(
            jti_hash=jti.ljust(64, "0"),
            user_id=user_id,
            expires_at=expires_at,
            revoked=revoked,
        )
    )


def test_cleanup_removes_expired_and_revoked_records_only() -> None:
    now = datetime.now(UTC)
    session = SessionLocal()
    user = _create_user(session, "maintenance-1@example.com")

    # Idempotency: one expired, one valid
    _add_idempotency_key(session, user.id, "expired-key", now - timedelta(hours=1))
    _add_idempotency_key(session, user.id, "valid-key", now + timedelta(hours=1))

    # Refresh tokens: expired, revoked, and valid
    _add_refresh_token(session, user.id, "expired-token", now - timedelta(days=1))
    _add_refresh_token(
        session, user.id, "revoked-token", now + timedelta(days=1), revoked=True
    )
    _add_refresh_token(session, user.id, "valid-token", now + timedelta(days=1))

    session.commit()
    session.close()

    session = SessionLocal()
    try:
        with UnitOfWork(lambda: session) as uow:
            result = run_temporary_data_cleanup(uow, now=now)
    finally:
        session.close()

    assert result == {"idempotency_keys": 1, "refresh_tokens": 2}

    # Valid records must be preserved
    session = SessionLocal()
    try:
        keys = session.execute(select(IdempotencyKey)).scalars().all()
        assert [k.key for k in keys] == ["valid-key"]

        tokens = session.execute(select(RefreshToken)).scalars().all()
        assert [t.jti_hash for t in tokens] == ["valid-token".ljust(64, "0")]
    finally:
        session.close()


def test_run_temporary_data_cleanup_now_cleans_via_own_session() -> None:
    now = datetime.now(UTC)
    session = SessionLocal()
    user = _create_user(session, "maintenance-2@example.com")
    _add_idempotency_key(session, user.id, "script-key", now - timedelta(hours=2))
    session.commit()
    session.close()

    result = run_temporary_data_cleanup_now()

    assert result["idempotency_keys"] >= 1
    assert result["refresh_tokens"] >= 0


def test_cleanup_scheduler_loop_runs_and_stops(monkeypatch) -> None:
    calls: list[int] = []

    def fake_cleanup(session_factory):
        calls.append(1)
        return {"idempotency_keys": 0, "refresh_tokens": 0}

    monkeypatch.setattr(
        scheduler_module, "run_temporary_data_cleanup_now", fake_cleanup
    )

    async def scenario() -> None:
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            scheduler_module.cleanup_scheduler_loop(
                session_factory=SessionLocal,
                interval_seconds=0.02,
                stop_event=stop_event,
            )
        )
        await asyncio.sleep(0.1)
        stop_event.set()
        await asyncio.wait_for(task, timeout=2)

    asyncio.run(scenario())

    assert len(calls) >= 2
