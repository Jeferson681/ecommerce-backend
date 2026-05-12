from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.exceptions import InvalidPasswordError, NotFoundError
from app.modules.user import use_cases
from app.modules.user.schemas import UserUpdate


class DummyUoW:
    def __init__(self) -> None:
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_get_user_raises_if_missing(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

        def get_by_id(self, _user_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "UserRepository", Repo)

    with pytest.raises(NotFoundError):
        use_cases.get_user(1, DummyUoW())


def test_list_users_returns_empty(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

        def list(self, limit: int = 20, offset: int = 0) -> list[object]:
            return []

    monkeypatch.setattr(use_cases, "UserRepository", Repo)

    result = use_cases.list_users(DummyUoW())
    assert result == []


def test_update_user_raises_if_missing(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

        def get_by_id(self, _user_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "UserRepository", Repo)

    with pytest.raises(NotFoundError):
        use_cases.update_user(1, UserUpdate(first_name="Ana"), DummyUoW())


def test_change_password_raises_if_missing(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

        def get_by_id(self, _user_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "UserRepository", Repo)

    with pytest.raises(NotFoundError):
        use_cases.change_password(1, "NovaSenha123!", DummyUoW())


def test_change_password_raises_invalid_policy(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

        def get_by_id(self, user_id: int) -> object:
            now = datetime.now(timezone.utc)
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

    monkeypatch.setattr(use_cases, "UserRepository", Repo)
    monkeypatch.setattr(use_cases, "validate_password_policy", lambda _: False)

    with pytest.raises(InvalidPasswordError):
        use_cases.change_password(1, "invalida", DummyUoW())


def test_delete_user_commits_when_exists(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            self.deleted = False

        def get_by_id(self, user_id: int) -> object:
            now = datetime.now(timezone.utc)
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
            self.deleted = True

    monkeypatch.setattr(use_cases, "UserRepository", Repo)

    uow = DummyUoW()
    result = use_cases.delete_user(1, uow)

    assert result is None
    assert uow.committed is True


def test_delete_user_raises_if_missing(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object):
            pass

        def get_by_id(self, _user_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "UserRepository", Repo)

    with pytest.raises(NotFoundError):
        use_cases.delete_user(1, DummyUoW())
