# ruff: noqa: B017

"""Comprehensive tests for Auth use cases — happy path, sad path, and validation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import AuthenticationError
from backend.app.modules.auth import services
from backend.app.modules.auth.schemas import LoginRequest, RefreshTokenRequest

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

    class FakeTokenRepo:
        def __init__(self, session):
            pass

        def create(self, token):
            return token

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(
        services, "verify_password", lambda plain, hashed: plain == "correct_password"
    )
    monkeypatch.setattr(
        services, "create_access_token", lambda data: "access_token_abc"
    )
    monkeypatch.setattr(
        services, "create_refresh_token", lambda data: "refresh_token_abc"
    )
    monkeypatch.setattr(
        services,
        "decode_refresh_token",
        lambda token: {"sub": "1", "jti": "abc123", "exp": 9999999999},
    )
    monkeypatch.setattr(services, "JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 30)
    monkeypatch.setattr(services, "jti_hash", lambda jti: "hashed_jti")
    monkeypatch.setattr(services, "RefreshTokenRepository", FakeTokenRepo)

    uow = SimpleNamespace(session=object(), commit=lambda: None)
    response = services.login("ana@mail.com", "correct_password", uow)

    assert response.access_token == "access_token_abc"
    assert response.refresh_token == "refresh_token_abc"
    assert response.token_type == "bearer"
    assert response.expires_in == 1800  # 30 * 60


def test_logout_with_valid_token(monkeypatch) -> None:
    """Logout with a valid refresh token does not raise an exception."""
    monkeypatch.setattr(
        services,
        "decode_refresh_token",
        lambda token: {
            "sub": "1",
            "jti": "abc123",
            "exp": 9999999999,
            "type": "refresh",
        },
    )
    monkeypatch.setattr(services, "jti_hash", lambda jti: "hashed_jti")

    class FakeRepo:
        def __init__(self, session):
            pass

        def get_by_jti_hash(self, jti_hash):
            return SimpleNamespace(id=1, revoked=False)

        def revoke(self, token_id):
            pass

    monkeypatch.setattr(services, "RefreshTokenRepository", FakeRepo)

    uow = SimpleNamespace(session=object(), commit=lambda: None)
    # Should not raise
    services.logout("valid_refresh_token", uow)


def test_refresh_access_token_with_valid_token(monkeypatch) -> None:
    """Exchanging a valid refresh token returns a new access token."""
    monkeypatch.setattr(
        services,
        "decode_refresh_token",
        lambda token: {
            "sub": "1",
            "jti": "abc123",
            "exp": 9999999999,
            "type": "refresh",
        },
    )
    monkeypatch.setattr(
        services, "create_access_token", lambda data: "new_access_token"
    )
    monkeypatch.setattr(
        services, "create_refresh_token", lambda data: "new_refresh_token"
    )
    monkeypatch.setattr(services, "JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 30)
    monkeypatch.setattr(services, "jti_hash", lambda jti: "hashed_jti")

    class FakeRepo:
        def __init__(self, session):
            pass

        def get_by_jti_hash(self, jti_hash):
            return SimpleNamespace(id=1, revoked=False)

        def revoke(self, token_id):
            pass

        def create(self, token):
            return token

    monkeypatch.setattr(services, "RefreshTokenRepository", FakeRepo)

    uow = SimpleNamespace(session=object(), commit=lambda: None)
    response = services.refresh_access_token("valid_token", uow)

    assert response.access_token == "new_access_token"
    assert response.refresh_token == "new_refresh_token"
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

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        services.login(
            "nonexistent@mail.com", "password", SimpleNamespace(session=object())
        )


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

    monkeypatch.setattr(services, "UserRepository", lambda s: Repo(s))
    monkeypatch.setattr(
        services, "verify_password", lambda plain, hashed: plain == "correct_password"
    )

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        services.login(
            "ana@mail.com", "wrong_password", SimpleNamespace(session=object())
        )


# ======================================================================
# SAD PATH – logout failures
# ======================================================================


def test_logout_with_invalid_token(monkeypatch) -> None:
    """Logout with an invalid token raises an exception."""

    def fake_decode(*args: object) -> object:
        from jose import JWTError

        raise JWTError("Invalid token")

    monkeypatch.setattr(services, "decode_refresh_token", fake_decode)

    with pytest.raises(Exception):
        services.logout(
            "invalid_token", SimpleNamespace(session=object(), commit=lambda: None)
        )


# ======================================================================
# SAD PATH – refresh failures
# ======================================================================


def test_refresh_with_invalid_token(monkeypatch) -> None:
    """Refresh with an invalid token raises AuthenticationError."""

    def fake_decode(*args: object) -> object:
        raise Exception("bad token")

    monkeypatch.setattr(services, "decode_refresh_token", fake_decode)

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        services.refresh_access_token(
            "bad_token", SimpleNamespace(session=object(), commit=lambda: None)
        )


def test_refresh_with_missing_sub_claim(monkeypatch) -> None:
    """Refresh with a token missing 'sub' claim raises AuthenticationError."""
    monkeypatch.setattr(
        services,
        "decode_refresh_token",
        lambda token: {"type": "refresh"},  # no 'sub' key
    )

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        services.refresh_access_token(
            "no_sub_token", SimpleNamespace(session=object(), commit=lambda: None)
        )


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
