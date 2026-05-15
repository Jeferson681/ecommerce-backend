from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from app.modules.user import use_cases
from app.modules.user.schemas import UserCreate, UserUpdate


class DummyRepo:
    def __init__(self, session: object):
        self.session = session
        self.created = False

    def create(self, user: object) -> object:
        self.created = True
        now = datetime.now(UTC)
        user.id = 1
        user.is_active = True
        user.created_at = now
        user.updated_at = now
        return user

    def get_by_id(self, user_id: int) -> object:
        now = datetime.now(UTC)
        return SimpleNamespace(
            id=user_id,
            first_name="Ana",
            last_name="Silva",
            email="ana@mail.com",
            password_hash="hashed:old",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def list(self, limit: int = 20, offset: int = 0) -> list[object]:
        now = datetime.now(UTC)
        return [
            SimpleNamespace(
                id=1,
                first_name="Ana",
                last_name="Silva",
                email="ana@mail.com",
                password_hash="hashed:1",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        ]

    def delete(self, user: object) -> None:
        return None


class DummyUoW:
    def __init__(self) -> None:
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_create_user_calls_repo_and_commit(monkeypatch) -> None:
    created: dict[str, DummyRepo] = {}

    def fake_repo_factory(session: object) -> DummyRepo:
        repo = DummyRepo(session)
        created["repo"] = repo
        return repo

    monkeypatch.setattr(use_cases, "UserRepository", fake_repo_factory)
    monkeypatch.setattr(use_cases, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(use_cases, "hash_password", lambda raw: f"hashed:{raw}")

    uow = DummyUoW()
    data = UserCreate(
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
        password="Abcd1234!",
    )

    user = use_cases.create_user(data, uow)

    assert created["repo"].created is True
    assert uow.committed is True
    assert user.id == 1


def test_get_user_returns_userread(monkeypatch) -> None:
    monkeypatch.setattr(use_cases, "UserRepository", DummyRepo)

    uow = DummyUoW()
    user = use_cases.get_user(10, uow)

    assert user.id == 10
    assert user.email == "ana@mail.com"


def test_list_users_returns_list(monkeypatch) -> None:
    monkeypatch.setattr(use_cases, "UserRepository", DummyRepo)

    uow = DummyUoW()
    users = use_cases.list_users(uow)

    assert len(users) == 1
    assert users[0].id == 1


def test_update_user_commits_and_updates_fields(monkeypatch) -> None:
    monkeypatch.setattr(use_cases, "UserRepository", DummyRepo)

    uow = DummyUoW()
    update = UserUpdate(first_name="Bea", is_active=False)

    user = use_cases.update_user(1, update, uow)

    assert uow.committed is True
    assert user.first_name == "Bea"
    assert user.is_active is False


def test_change_password_commits_and_hashes(monkeypatch) -> None:
    monkeypatch.setattr(use_cases, "UserRepository", DummyRepo)
    monkeypatch.setattr(use_cases, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(use_cases, "hash_password", lambda raw: f"hashed:{raw}")

    uow = DummyUoW()
    user = use_cases.change_password(1, "NovaSenha123!", uow)

    assert uow.committed is True
    assert user.id == 1
