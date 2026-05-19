from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import AuthenticationError
from backend.app.modules.auth import use_cases


class DummyUserRepo:
    def __init__(self, session: object):
        self.session = session

    def get_by_email(self, email: str) -> object | None:
        if email == "ana@mail.com":
            return SimpleNamespace(
                id=1,
                first_name="Ana",
                last_name="Silva",
                email="ana@mail.com",
                password_hash="hashed:correct_password",
                is_active=True,
            )
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


def test_login_with_valid_credentials(monkeypatch) -> None:
    """Test successful login with valid email and password."""
    monkeypatch.setattr(use_cases, "UserRepository", DummyUserRepo)
    monkeypatch.setattr(
        use_cases, "verify_password", lambda plain, hashed: plain == "correct_password"
    )
    monkeypatch.setattr(use_cases, "create_access_token", lambda data: "access_token")
    monkeypatch.setattr(use_cases, "create_refresh_token", lambda data: "refresh_token")

    uow = DummyUoW()
    response = use_cases.login("ana@mail.com", "correct_password", uow)

    assert response.access_token == "access_token"
    assert response.refresh_token == "refresh_token"
    assert response.token_type == "bearer"
    assert response.expires_in is not None


def test_login_with_invalid_email(monkeypatch) -> None:
    """Test login with non-existent email."""
    monkeypatch.setattr(use_cases, "UserRepository", DummyUserRepo)
    monkeypatch.setattr(
        use_cases, "verify_password", lambda plain, hashed: plain == "correct_password"
    )

    uow = DummyUoW()

    with pytest.raises(AuthenticationError):
        use_cases.login("nonexistent@mail.com", "password", uow)


def test_login_with_invalid_password(monkeypatch) -> None:
    """Test login with incorrect password."""
    monkeypatch.setattr(use_cases, "UserRepository", DummyUserRepo)
    monkeypatch.setattr(
        use_cases, "verify_password", lambda plain, hashed: plain == "correct_password"
    )

    uow = DummyUoW()

    with pytest.raises(AuthenticationError):
        use_cases.login("ana@mail.com", "wrong_password", uow)


def test_logout_with_valid_token(monkeypatch) -> None:
    """Test logout with valid refresh token."""
    monkeypatch.setattr(
        use_cases,
        "decode_refresh_token",
        lambda token: {"sub": "1", "type": "refresh"},
    )

    uow = DummyUoW()
    # Should not raise an exception
    use_cases.logout("valid_refresh_token", uow)


def test_logout_with_invalid_token(monkeypatch) -> None:
    """Test logout with invalid refresh token."""
    from jose import JWTError

    def fake_decode(*args):
        raise JWTError("Invalid token")

    monkeypatch.setattr(use_cases, "decode_refresh_token", fake_decode)

    uow = DummyUoW()

    with pytest.raises(JWTError):
        use_cases.logout("invalid_token", uow)
