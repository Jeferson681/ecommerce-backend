from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.modules.user import use_cases
from app.modules.user.schemas import UserCreate, UserUpdate


class DummyUoW:
    def __init__(self) -> None:
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_create_user_rolls_back_on_repo_error(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

        def create(self, _user: object) -> object:
            raise RuntimeError("db error")

    monkeypatch.setattr(use_cases, "UserRepository", Repo)
    monkeypatch.setattr(use_cases, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(use_cases, "hash_password", lambda raw: f"hashed:{raw}")

    uow = DummyUoW()
    data = UserCreate(
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
        password="Abcd1234!",
    )

    with pytest.raises(RuntimeError):
        use_cases.create_user(data, uow)

    assert uow.rolled_back is True


def test_update_user_rolls_back_on_commit_error(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

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

    class FailingUoW(DummyUoW):
        def commit(self) -> None:
            raise RuntimeError("commit fail")

    monkeypatch.setattr(use_cases, "UserRepository", Repo)

    with pytest.raises(RuntimeError):
        use_cases.update_user(1, UserUpdate(first_name="Nova"), FailingUoW())


def test_change_password_rolls_back_on_commit_error(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

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

    class FailingUoW(DummyUoW):
        def commit(self) -> None:
            raise RuntimeError("commit fail")

    monkeypatch.setattr(use_cases, "UserRepository", Repo)
    monkeypatch.setattr(use_cases, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(use_cases, "hash_password", lambda raw: f"hashed:{raw}")

    with pytest.raises(RuntimeError):
        use_cases.change_password(1, "NovaSenha123!", FailingUoW())


def test_delete_user_rolls_back_on_repo_error(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

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

        def delete(self, _user: object) -> None:
            raise RuntimeError("delete fail")

    monkeypatch.setattr(use_cases, "UserRepository", Repo)

    uow = DummyUoW()
    with pytest.raises(RuntimeError):
        use_cases.delete_user(1, uow)

    assert uow.rolled_back is True
