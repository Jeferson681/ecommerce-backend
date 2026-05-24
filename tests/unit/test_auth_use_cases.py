# ruff: noqa: B017

"""Comprehensive tests for Auth use cases — happy path, sad path, and validation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import AuthenticationError
from backend.app.modules.auth import use_cases
from backend.app.modules.auth.schemas import LoginRequest, RefreshTokenRequest

from .conftest import DummyUoW

# ======================================================================
# HAPPY PATH
# ======================================================================


def test_login_with_valid_credentials(monkeypatch) -> None:
    """Successful login returns TokenResponse with access and refresh tokens."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_email(self, email: str) -> SimpleNamespace | None:
            return SimpleNamespace(
                id=1,
                first_name="Ana",
                last_name="Silva",
                email="ana@mail.com",
                password_hash="hashed:correct_password",
                is_active=True,
            )

    monkeypatch.setattr(use_cases, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(
        use_cases, "verify_password", lambda plain, hashed: plain == "correct_password"
    )
    monkeypatch.setattr(
        use_cases, "create_access_token", lambda data: "access_token_abc"
    )
    monkeypatch.setattr(
        use_cases, "create_refresh_token", lambda data: "refresh_token_abc"
    )
    monkeypatch.setattr(use_cases, "JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 30)

    uow = DummyUoW()
    response = use_cases.login("ana@mail.com", "correct_password", uow)

    assert response.access_token == "access_token_abc"
    assert response.refresh_token == "refresh_token_abc"
    assert response.token_type == "bearer"
    assert response.expires_in == 1800  # 30 * 60


def test_logout_with_valid_token(monkeypatch) -> None:
    """Logout with a valid refresh token does not raise an exception."""
    monkeypatch.setattr(
        use_cases,
        "decode_refresh_token",
        lambda token: {"sub": "1", "type": "refresh"},
    )

    # Should not raise
    use_cases.logout("valid_refresh_token", DummyUoW())


def test_refresh_access_token_with_valid_token(monkeypatch) -> None:
    """Exchanging a valid refresh token returns a new access token."""
    monkeypatch.setattr(
        use_cases,
        "decode_refresh_token",
        lambda token: {"sub": "1", "type": "refresh"},
    )
    monkeypatch.setattr(
        use_cases, "create_access_token", lambda data: "new_access_token"
    )
    monkeypatch.setattr(use_cases, "JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 30)

    response = use_cases.refresh_access_token("valid_token", DummyUoW())

    assert response.access_token == "new_access_token"
    assert response.refresh_token == "valid_token"
    assert response.token_type == "bearer"
    assert response.expires_in == 1800


# ======================================================================
# SAD PATH – login failures
# ======================================================================


def test_login_with_invalid_email(monkeypatch) -> None:
    """Login with non-existent email raises AuthenticationError."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_email(self, email: str) -> None:
            return None

    monkeypatch.setattr(use_cases, "UserRepository", lambda s: Repo(s))

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        use_cases.login("nonexistent@mail.com", "password", DummyUoW())


def test_login_with_invalid_password(monkeypatch) -> None:
    """Login with incorrect password raises AuthenticationError."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_email(self, email: str) -> SimpleNamespace:
            return SimpleNamespace(
                id=1,
                first_name="Ana",
                last_name="Silva",
                email="ana@mail.com",
                password_hash="hashed:correct_password",
                is_active=True,
            )

    monkeypatch.setattr(use_cases, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(
        use_cases, "verify_password", lambda plain, hashed: plain == "correct_password"
    )

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        use_cases.login("ana@mail.com", "wrong_password", DummyUoW())


# ======================================================================
# SAD PATH – logout failures
# ======================================================================


def test_logout_with_invalid_token(monkeypatch) -> None:
    """Logout with an invalid token raises an exception."""

    def fake_decode(*args: object) -> object:
        from jose import JWTError

        raise JWTError("Invalid token")

    monkeypatch.setattr(use_cases, "decode_refresh_token", fake_decode)

    with pytest.raises(Exception):
        use_cases.logout("invalid_token", DummyUoW())


# ======================================================================
# SAD PATH – refresh failures
# ======================================================================


def test_refresh_with_invalid_token(monkeypatch) -> None:
    """Refresh with an invalid token raises AuthenticationError."""

    def fake_decode(*args: object) -> object:
        raise Exception("bad token")

    monkeypatch.setattr(use_cases, "decode_refresh_token", fake_decode)

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        use_cases.refresh_access_token("bad_token", DummyUoW())


def test_refresh_with_missing_sub_claim(monkeypatch) -> None:
    """Refresh with a token missing 'sub' claim raises AuthenticationError."""
    monkeypatch.setattr(
        use_cases,
        "decode_refresh_token",
        lambda token: {"type": "refresh"},  # no 'sub' key
    )

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        use_cases.refresh_access_token("no_sub_token", DummyUoW())


# ======================================================================
# VALIDATION – schema tests
# ======================================================================


def test_login_request_valid() -> None:
    """Valid login request is accepted."""
    data = LoginRequest(email="test@example.com", password="secret123")
    assert data.email == "test@example.com"
    assert data.password == "secret123"


def test_login_request_invalid_email() -> None:
    """Invalid email in login request raises validation error."""
    with pytest.raises(Exception):
        LoginRequest(email="not-an-email", password="secret123")


def test_refresh_token_request_valid() -> None:
    """Valid refresh token request is accepted."""
    data = RefreshTokenRequest(refresh_token="some_token")
    assert data.refresh_token == "some_token"


def test_refresh_token_request_missing_field() -> None:
    """Missing refresh_token field raises validation error."""
    with pytest.raises(Exception):
        RefreshTokenRequest()  # type: ignore[call-arg]
