from backend.app.core.database import Base, SessionLocal, engine
from backend.app.idempotency.repository import IdempotencyKeyRepository
from backend.app.idempotency.service import create_idempotency_record


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def test_get_or_create_creates_new_record() -> None:
    session = SessionLocal()
    repo = IdempotencyKeyRepository(session)

    record, created = repo.get_or_create(
        create_idempotency_record("k-repo-1", user_id=1, request_hash="h1")
    )

    assert created is True
    assert record.key == "k-repo-1"


def test_get_or_create_returns_existing_when_present() -> None:
    session = SessionLocal()
    repo = IdempotencyKeyRepository(session)

    # create initial record
    original = create_idempotency_record("k-repo-2", user_id=1, request_hash="h2")
    repo.create(original)
    session.commit()

    record, created = repo.get_or_create(
        create_idempotency_record("k-repo-2", user_id=1, request_hash="h2")
    )

    assert created is False
    assert record.key == "k-repo-2"
