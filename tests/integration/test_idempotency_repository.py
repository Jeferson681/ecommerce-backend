from datetime import UTC, datetime, timedelta

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
                first_name="Repo",
                last_name="User",
                email="repo-user@example.com",
                password_hash="x",
            )
        )
        session.commit()
    finally:
        session.close()


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def test_claim_creates_new_record() -> None:
    session = SessionLocal()
    repo = IdempotencyRepository(session)
    try:
        record, created = repo.claim(
            IdempotencyKey(
                key="k-repo-1",
                user_id=1,
                request_hash="h1",
                response_status=None,
                response_body=None,
                expires_at=datetime.now(UTC)
                + timedelta(hours=DEFAULT_EXPIRATION_HOURS),
            )
        )

        assert created is True
        assert record.key == "k-repo-1"
    finally:
        session.close()


def test_claim_returns_existing_when_present() -> None:
    session = SessionLocal()
    repo = IdempotencyRepository(session)
    try:
        # create initial record
        repo.claim(
            IdempotencyKey(
                key="k-repo-2",
                user_id=1,
                request_hash="h2",
                response_status=None,
                response_body=None,
                expires_at=datetime.now(UTC)
                + timedelta(hours=DEFAULT_EXPIRATION_HOURS),
            )
        )

        record, created = repo.claim(
            IdempotencyKey(
                key="k-repo-2",
                user_id=1,
                request_hash="h2",
                response_status=None,
                response_body=None,
                expires_at=datetime.now(UTC)
                + timedelta(hours=DEFAULT_EXPIRATION_HOURS),
            )
        )

        assert created is False
        assert record.key == "k-repo-2"
    finally:
        session.close()
