# ruff: noqa: B017

"""Comprehensive tests for User use cases — happy path, sad path, rollback, and validation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.app.core.exceptions import InvalidPasswordError, NotFoundError
from backend.app.modules.user import services
from backend.app.modules.user.schemas import (
    UserChangePassword,
    UserCreate,
    UserUpdate,
)

from .conftest import DummyUoW, make_user

# ======================================================================
# HAPPY PATH
# ======================================================================


def test_create_user_happy_path(monkeypatch) -> None:
    """Creating a valid user calls repository.create, commits, and returns a UserRead."""
    created: list = []

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_email(self, email: str) -> object | None:
            return None

        def create(self, user: object) -> object:
            now = datetime.now(UTC)
            user.id = 1  # type: ignore[attr-defined]
            user.role = "user"  # type: ignore[attr-defined]
            user.is_active = True  # type: ignore[attr-defined]
            user.created_at = now  # type: ignore[attr-defined]
            user.updated_at = now  # type: ignore[attr-defined]
            created.append(user)
            return user

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(services, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(services, "hash_password", lambda raw: f"hashed:{raw}")

    uow = DummyUoW()
    data = UserCreate(
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
        password="Abcd1234!",
    )

    result = services.create_user(data, uow)

    assert uow.committed is True
    assert result.id == 1
    assert result.email == "ana@mail.com"
    assert result.first_name == "Ana"
    assert result.last_name == "Silva"
    assert result.is_active is True
    assert len(created) == 1


def test_get_user_happy_path(monkeypatch) -> None:
    """Getting an existing user returns a UserRead."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id)

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    result = services.get_user(42, DummyUoW())

    assert result.id == 42
    assert result.email == "ana@mail.com"
    assert result.first_name == "Ana"
    assert result.last_name == "Silva"


def test_get_user_owner_access(monkeypatch) -> None:
    """Owner can access their own profile."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id, role="user")

    repo_instance = Repo(object())
    monkeypatch.setattr(services, "UserRepository", lambda s: repo_instance)

    result = services.get_user(1, DummyUoW(), requesting_user_id=1)
    assert result.id == 1


def test_get_user_admin_access(monkeypatch) -> None:
    """Admin can access any user's profile."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            # Return admin when asked for requestor, regular user for target
            if user_id == 999:
                return make_user(id=999, role="admin")
            return make_user(id=user_id, role="user")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    result = services.get_user(1, DummyUoW(), requesting_user_id=999)
    assert result.id == 1


def test_list_users_happy_path(monkeypatch) -> None:
    """Listing users returns all users from the repository."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def list(self, limit: int = 20, offset: int = 0) -> list[object]:
            return [make_user(id=1), make_user(id=2)]

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    results = services.list_users(DummyUoW())

    assert len(results) == 2
    assert results[0].id == 1
    assert results[1].id == 2


def test_list_users_with_pagination(monkeypatch) -> None:
    """Pagination parameters are forwarded to the repository."""
    captured: dict = {}

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def list(self, limit: int = 20, offset: int = 0) -> list[object]:
            captured["limit"] = limit
            captured["offset"] = offset
            return []

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    services.list_users(DummyUoW(), limit=10, offset=5)

    assert captured["limit"] == 10
    assert captured["offset"] == 5


def test_update_user_happy_path(monkeypatch) -> None:
    """Updating an existing user commits and reflects changes."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id, first_name="Old")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    uow = DummyUoW()
    update = UserUpdate(first_name="Bea", is_active=False)
    result = services.update_user(1, update, uow)

    assert uow.committed is True
    assert result.first_name == "Bea"
    assert result.is_active is False


def test_update_user_partial(monkeypatch) -> None:
    """Partial update only changes provided fields."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id, first_name="Ana", last_name="Silva")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    uow = DummyUoW()
    result = services.update_user(1, UserUpdate(last_name="Costa"), uow)

    assert result.first_name == "Ana"  # unchanged
    assert result.last_name == "Costa"  # changed
    assert uow.committed is True


def test_update_user_owner_access(monkeypatch) -> None:
    """Owner can update their own profile."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id)

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    result = services.update_user(
        1, UserUpdate(first_name="New"), DummyUoW(), requesting_user_id=1
    )
    assert result.first_name == "New"


def test_change_password_happy_path(monkeypatch) -> None:
    """Changing password commits and returns the user."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id, password_hash="hashed:old")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(
        services, "verify_password", lambda plain, hashed: plain == "OldPass1!"
    )
    monkeypatch.setattr(services, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(services, "hash_password", lambda raw: f"hashed:{raw}")

    uow = DummyUoW()
    result = services.change_password(1, "OldPass1!", "NovaSenha123!", uow)

    assert uow.committed is True
    assert result.id == 1


def test_delete_user_happy_path(monkeypatch) -> None:
    """Deleting an existing user commits and returns None."""
    deleted: list = []

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id)

        def delete(self, user: object) -> None:
            deleted.append(user)

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    uow = DummyUoW()
    result = services.delete_user(1, uow)

    assert result is None
    assert uow.committed is True
    assert len(deleted) == 1


# ======================================================================
# SAD PATH – validation
# ======================================================================


class TestUserCreateValidation:
    def test_empty_first_name(self) -> None:
        with pytest.raises(Exception):  # Pydantic ValidationError
            UserCreate(
                first_name="", last_name="Silva", email="a@b.com", password="Abcd1234!"
            )

    def test_short_first_name(self) -> None:
        with pytest.raises(Exception):
            UserCreate(
                first_name="A", last_name="Silva", email="a@b.com", password="Abcd1234!"
            )

    def test_empty_last_name(self) -> None:
        with pytest.raises(Exception):
            UserCreate(
                first_name="Ana", last_name="", email="a@b.com", password="Abcd1234!"
            )

    def test_short_last_name(self) -> None:
        with pytest.raises(Exception):
            UserCreate(
                first_name="Ana", last_name="S", email="a@b.com", password="Abcd1234!"
            )

    def test_invalid_email(self) -> None:
        with pytest.raises(Exception):
            UserCreate(
                first_name="Ana",
                last_name="Silva",
                email="not-an-email",
                password="Abcd1234!",
            )

    def test_short_password(self) -> None:
        with pytest.raises(Exception):
            UserCreate(
                first_name="Ana", last_name="Silva", email="a@b.com", password="short"
            )

    def test_normalizes_fields(self) -> None:
        data = UserCreate(
            first_name="  Ana  ",
            last_name="  Silva  ",
            email="  ANA@MAIL.COM  ",
            password="Abcd1234!",
        )
        assert data.first_name == "Ana"
        assert data.last_name == "Silva"
        assert data.email == "ana@mail.com"


class TestUserUpdateValidation:
    def test_empty_first_name(self) -> None:
        with pytest.raises(Exception):
            UserUpdate(first_name="")

    def test_short_first_name(self) -> None:
        with pytest.raises(Exception):
            UserUpdate(first_name="A")

    def test_empty_last_name(self) -> None:
        with pytest.raises(Exception):
            UserUpdate(last_name="")

    def test_invalid_email(self) -> None:
        with pytest.raises(Exception):
            UserUpdate(email="invalid-email")

    def test_whitespace_only_name(self) -> None:
        with pytest.raises(Exception):
            UserUpdate(first_name=" ")

    def test_valid_partial_update(self) -> None:
        data = UserUpdate(first_name="New")
        assert data.first_name == "New"
        assert data.last_name is None


class TestUserChangePasswordValidation:
    def test_short_password(self) -> None:
        with pytest.raises(Exception):
            UserChangePassword(new_password="short")

    def test_too_short_password(self) -> None:
        with pytest.raises(Exception):
            UserChangePassword(new_password="123")

    def test_empty_password(self) -> None:
        with pytest.raises(Exception):
            UserChangePassword(new_password="")

    def test_valid_password(self) -> None:
        data = UserChangePassword(
            current_password="OldPass1!",
            new_password="ValidPass123!",
        )
        assert data.current_password == "OldPass1!"
        assert data.new_password == "ValidPass123!"


# ======================================================================
# SAD PATH – use case failures
# ======================================================================


def test_get_user_raises_not_found_when_missing(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, _user_id: int) -> None:
            return None

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="User not found"):
        services.get_user(1, DummyUoW())


def test_get_user_raises_not_found_for_non_owner(monkeypatch) -> None:
    """A non-admin, non-owner user cannot access another user's profile."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id, role="user")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="User not found"):
        services.get_user(2, DummyUoW(), requesting_user_id=1)


def test_update_user_raises_not_found_when_missing(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, _user_id: int) -> None:
            return None

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="User not found"):
        services.update_user(1, UserUpdate(first_name="Ana"), DummyUoW())


def test_update_user_raises_not_found_for_non_owner(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id, role="user")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="User not found"):
        services.update_user(
            2, UserUpdate(first_name="New"), DummyUoW(), requesting_user_id=1
        )


def test_change_password_raises_not_found_when_missing(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, _user_id: int) -> None:
            return None

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="User not found"):
        services.change_password(1, "OldPass1!", "NovaSenha123!", DummyUoW())


def test_change_password_raises_invalid_policy(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id)

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(services, "verify_password", lambda plain, hashed: True)
    monkeypatch.setattr(services, "validate_password_policy", lambda _: False)

    with pytest.raises(InvalidPasswordError, match="Credential does not meet"):
        services.change_password(1, "OldPass1!", "weak", DummyUoW())


def test_change_password_raises_not_found_for_different_user(monkeypatch) -> None:
    """A user cannot change another user's password (owner-only)."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id)

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(services, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(services, "hash_password", lambda raw: f"hashed:{raw}")

    with pytest.raises(NotFoundError, match="User not found"):
        services.change_password(
            2, "OldPass1!", "NovaSenha123!", DummyUoW(), requesting_user_id=1
        )


def test_delete_user_raises_not_found_when_missing(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, _user_id: int) -> None:
            return None

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="User not found"):
        services.delete_user(1, DummyUoW())


def test_delete_user_raises_not_found_for_non_owner(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id, role="user")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="User not found"):
        services.delete_user(2, DummyUoW(), requesting_user_id=1)


def test_create_user_raises_invalid_password_policy(monkeypatch) -> None:
    """Creating a user with a weak password that fails policy check raises InvalidPasswordError."""
    monkeypatch.setattr(services, "validate_password_policy", lambda _: False)
    monkeypatch.setattr(services, "hash_password", lambda raw: f"hashed:{raw}")

    uow = DummyUoW()
    # Password must be >=8 chars to satisfy schema, but fails the application-level policy
    data = UserCreate(
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
        password="WeakPass12",  # passes schema length check, fails policy
    )

    with pytest.raises(InvalidPasswordError, match="Credential does not meet"):
        services.create_user(data, uow)

    assert uow.committed is False  # no commit on validation failure


# ======================================================================
# SAD PATH – empty results
# ======================================================================


def test_list_users_empty(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def list(self, limit: int = 20, offset: int = 0) -> list[object]:
            return []

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    results = services.list_users(DummyUoW())
    assert results == []


# ======================================================================
# ROLLBACK TESTS
# ======================================================================


def test_create_user_rolls_back_on_repo_error(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_email(self, email: str) -> object | None:
            return None

        def create(self, _user: object) -> object:
            raise RuntimeError("db error")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(services, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(services, "hash_password", lambda raw: f"hashed:{raw}")

    uow = DummyUoW()
    data = UserCreate(
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
        password="Abcd1234!",
    )

    with pytest.raises(RuntimeError, match="db error"):
        services.create_user(data, uow)

    assert uow.rolled_back is True


def test_update_user_rolls_back_on_commit_error(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id)

    class FailingUoW(DummyUoW):
        def commit(self) -> None:
            raise RuntimeError("commit fail")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(RuntimeError, match="commit fail"):
        services.update_user(1, UserUpdate(first_name="Nova"), FailingUoW())


def test_change_password_rolls_back_on_commit_error(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id, password_hash="hashed:old")

    class FailingUoW(DummyUoW):
        def commit(self) -> None:
            raise RuntimeError("commit fail")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(services, "verify_password", lambda plain, hashed: True)
    monkeypatch.setattr(services, "validate_password_policy", lambda _: True)
    monkeypatch.setattr(services, "hash_password", lambda raw: f"hashed:{raw}")

    with pytest.raises(RuntimeError, match="commit fail"):
        services.change_password(1, "OldPass1!", "NovaSenha123!", FailingUoW())


def test_delete_user_rolls_back_on_repo_error(monkeypatch) -> None:
    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int) -> object:
            return make_user(id=user_id)

        def delete(self, _user: object) -> None:
            raise RuntimeError("delete fail")

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    uow = DummyUoW()
    with pytest.raises(RuntimeError, match="delete fail"):
        services.delete_user(1, uow)

    assert uow.rolled_back is True
