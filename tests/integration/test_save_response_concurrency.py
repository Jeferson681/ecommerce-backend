import threading
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.idempotency.domain.models import IdempotencyKey
from backend.app.idempotency.repositories import IdempotencyRepository
from backend.app.modules.user.domain.models import User

DEFAULT_EXPIRATION_HOURS = 24


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        session.add(
            User(
                id=1,
                first_name="Save",
                last_name="User",
                email="save-user@example.com",
                password_hash="x",
            )
        )
        session.commit()
    finally:
        session.close()


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


@pytest.mark.integration
def test_save_response_concurrent_writers() -> None:
    key = "k-save-1"
    user_id = 1

    # create initial idempotency record
    session = SessionLocal()
    try:
        session.add(
            IdempotencyKey(
                key=key,
                user_id=user_id,
                request_hash="h-save",
                response_status=None,
                response_body=None,
                expires_at=datetime.now(UTC)
                + timedelta(hours=DEFAULT_EXPIRATION_HOURS),
            )
        )
        session.commit()
    finally:
        session.close()

    results: list[tuple[str, bool]] = []
    barrier = threading.Barrier(2)

    def worker(body: str):
        session = SessionLocal()
        try:
            repo = IdempotencyRepository(session)
            barrier.wait()
            success = repo.save_response(key, user_id, 201, body)
            if success:
                session.commit()
            else:
                session.rollback()
            results.append((body, success))
        finally:
            session.close()

    t1 = threading.Thread(target=worker, args=("body-a",))
    t2 = threading.Thread(target=worker, args=("body-b",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # exactly one writer should have succeeded
    assert sum(1 for _, ok in results if ok) == 1

    # DB must contain the response written by the winning writer
    session = SessionLocal()
    try:
        rec = session.execute(
            select(IdempotencyKey).where(IdempotencyKey.key == key)
        ).scalar_one()
        assert rec.response_body in ("body-a", "body-b")
        assert rec.response_status == 201
    finally:
        session.close()
