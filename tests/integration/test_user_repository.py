from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.modules.user.domain.models import User
from app.modules.user.repositories.user_repository import UserRepository

SessionLocal: sessionmaker[Session]


def setup_module(module: object) -> None:
    module.engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=module.engine)
    global SessionLocal
    SessionLocal = sessionmaker(bind=module.engine, future=True)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=module.engine)


def test_user_repository_crud_flow() -> None:
    session = SessionLocal()
    repo = UserRepository(session)

    user = User(
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
        password_hash="hashed:abc",
    )
    repo.create(user)
    session.commit()

    fetched = repo.get_by_id(user.id)
    assert fetched is not None

    listed = repo.list()
    assert len(listed) >= 1

    user.first_name = "Beatriz"
    repo.update(user)
    session.commit()

    updated = repo.get_by_id(user.id)
    assert updated is not None
    assert updated.first_name == "Beatriz"

    repo.delete(user)
    session.commit()

    deleted = repo.get_by_id(user.id)
    assert deleted is None


def test_user_repository_list_pagination_and_missing() -> None:
    session = SessionLocal()
    repo = UserRepository(session)

    users = [
        User(
            first_name="U1",
            last_name="Test",
            email="u1@mail.com",
            password_hash="hashed:1",
        ),
        User(
            first_name="U2",
            last_name="Test",
            email="u2@mail.com",
            password_hash="hashed:2",
        ),
        User(
            first_name="U3",
            last_name="Test",
            email="u3@mail.com",
            password_hash="hashed:3",
        ),
    ]
    for user in users:
        repo.create(user)
    session.commit()

    page = repo.list(limit=2, offset=1)
    assert len(page) == 2

    missing = repo.get_by_id(999999)
    assert missing is None
