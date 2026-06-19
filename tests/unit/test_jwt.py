"""Unit tests for JWT token hardening (Phase 2).

Covers:
- Invalid audience -> decode must fail
- Invalid issuer -> decode must fail
- Valid token -> decode succeeds with correct claims
- Expired token -> decode must fail
- jti, iat, iss, aud claims present in both access and refresh tokens
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from jose import JWTError, jwt as jose_jwt

# Ensure JWT_SECRET_KEY is available before importing settings
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")

from backend.app.core.config import Settings  # noqa: E402
from backend.app.modules.auth import tokens as token_module  # noqa: E402

# Create a dedicated Settings instance with deterministic values for tests
_test_settings = Settings(
    JWT_SECRET_KEY="test-jwt-secret",
    JWT_ISSUER="test-issuer",
    JWT_AUDIENCE="test-audience",
)


@pytest.fixture(autouse=True)
def _use_test_settings(monkeypatch):
    """Override application settings with test values for all tests."""
    monkeypatch.setattr(
        token_module.settings,
        "JWT_SECRET_KEY",
        _test_settings.JWT_SECRET_KEY,
    )
    monkeypatch.setattr(
        token_module.settings,
        "JWT_ISSUER",
        _test_settings.JWT_ISSUER,
    )
    monkeypatch.setattr(
        token_module.settings,
        "JWT_AUDIENCE",
        _test_settings.JWT_AUDIENCE,
    )

    import backend.app.core.config as cfg

    monkeypatch.setattr(
        cfg.settings,
        "JWT_SECRET_KEY",
        _test_settings.JWT_SECRET_KEY,
    )
    monkeypatch.setattr(
        cfg.settings,
        "JWT_ISSUER",
        _test_settings.JWT_ISSUER,
    )
    monkeypatch.setattr(
        cfg.settings,
        "JWT_AUDIENCE",
        _test_settings.JWT_AUDIENCE,
    )


# ======================================================================
# Claim Presence
# ======================================================================


class TestTokenClaims:
    """Verify that jti, iat, iss, and aud claims are present."""

    def test_access_token_has_all_required_claims(self) -> None:
        """Access token contains all required claims."""
        token = token_module.create_access_token({"sub": "1"})

        payload = jose_jwt.decode(
            token,
            _test_settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_iss": False, "verify_aud": False},
        )

        assert "jti" in payload
        assert "iat" in payload
        assert "iss" in payload
        assert "aud" in payload

        assert payload["sub"] == "1"
        assert payload["iss"] == _test_settings.JWT_ISSUER
        assert payload["aud"] == _test_settings.JWT_AUDIENCE

    def test_refresh_token_has_all_required_claims(self) -> None:
        """Refresh token contains all required claims."""
        token = token_module.create_refresh_token({"sub": "1"})

        payload = jose_jwt.decode(
            token,
            _test_settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_iss": False, "verify_aud": False},
        )

        assert "jti" in payload
        assert "iat" in payload
        assert "iss" in payload
        assert "aud" in payload

        assert payload["type"] == "refresh"
        assert payload["sub"] == "1"
        assert payload["iss"] == _test_settings.JWT_ISSUER
        assert payload["aud"] == _test_settings.JWT_AUDIENCE


# ======================================================================
# Issuer Validation (iss)
# ======================================================================


class TestIssuerValidation:
    """Invalid issuer should cause token decoding to fail."""

    def test_access_token_wrong_issuer_fails(self) -> None:
        """Access token with an unexpected issuer must fail validation."""
        wrong_claims = token_module._build_claims({"sub": "1"})
        wrong_claims["iss"] = "attacker-issuer"
        wrong_claims["exp"] = token_module._now() + timedelta(minutes=30)

        raw_token = jose_jwt.encode(
            wrong_claims,
            _test_settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        with pytest.raises(JWTError, match="Invalid token"):
            token_module.decode_access_token(raw_token)

    def test_refresh_token_wrong_issuer_fails(self) -> None:
        """Refresh token with an unexpected issuer must fail validation."""
        wrong_claims = token_module._build_claims({"sub": "1"})
        wrong_claims["type"] = "refresh"
        wrong_claims["iss"] = "attacker-issuer"
        wrong_claims["exp"] = token_module._now() + timedelta(days=7)

        raw_token = jose_jwt.encode(
            wrong_claims,
            _test_settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        with pytest.raises(JWTError, match="Invalid refresh token"):
            token_module.decode_refresh_token(raw_token)


# ======================================================================
# Audience Validation (aud)
# ======================================================================


class TestAudienceValidation:
    """Invalid audience should cause token decoding to fail."""

    def test_access_token_wrong_audience_fails(self) -> None:
        """Access token with an unexpected audience must fail validation."""
        wrong_claims = token_module._build_claims({"sub": "1"})
        wrong_claims["aud"] = "attacker-audience"
        wrong_claims["exp"] = token_module._now() + timedelta(minutes=30)

        raw_token = jose_jwt.encode(
            wrong_claims,
            _test_settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        with pytest.raises(JWTError, match="Invalid token"):
            token_module.decode_access_token(raw_token)

    def test_refresh_token_wrong_audience_fails(self) -> None:
        """Refresh token with an unexpected audience must fail validation."""
        wrong_claims = token_module._build_claims({"sub": "1"})
        wrong_claims["type"] = "refresh"
        wrong_claims["aud"] = "attacker-audience"
        wrong_claims["exp"] = token_module._now() + timedelta(days=7)

        raw_token = jose_jwt.encode(
            wrong_claims,
            _test_settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        with pytest.raises(JWTError, match="Invalid refresh token"):
            token_module.decode_refresh_token(raw_token)


# ======================================================================
# Valid Tokens
# ======================================================================


class TestValidToken:
    """Valid tokens should decode successfully."""

    def test_valid_access_token_decodes(self) -> None:
        """Valid access token decodes and returns expected claims."""
        token = token_module.create_access_token({"sub": "42"})

        payload = token_module.decode_access_token(token)

        assert payload["sub"] == "42"
        assert payload["iss"] == _test_settings.JWT_ISSUER
        assert payload["aud"] == _test_settings.JWT_AUDIENCE

        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload

    def test_valid_refresh_token_decodes(self) -> None:
        """Valid refresh token decodes and returns expected claims."""
        token = token_module.create_refresh_token({"sub": "42"})

        payload = token_module.decode_refresh_token(token)

        assert payload["sub"] == "42"
        assert payload["type"] == "refresh"
        assert payload["iss"] == _test_settings.JWT_ISSUER
        assert payload["aud"] == _test_settings.JWT_AUDIENCE

        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload


# ======================================================================
# Expired Tokens
# ======================================================================


class TestExpiredToken:
    """Expired tokens should fail validation."""

    def test_expired_access_token_fails(self) -> None:
        """Expired access token must fail validation."""
        with patch.object(
            token_module,
            "_now",
            return_value=datetime.now(UTC) - timedelta(minutes=60),
        ):
            token = token_module.create_access_token(
                {"sub": "1"},
                expires_delta=1,
            )

        with pytest.raises(JWTError, match="Invalid token"):
            token_module.decode_access_token(token)

    def test_expired_refresh_token_fails(self) -> None:
        """Expired refresh token must fail validation."""
        with patch.object(
            token_module,
            "_now",
            return_value=datetime.now(UTC) - timedelta(days=10),
        ):
            token = token_module.create_refresh_token(
                {"sub": "1"},
                expires_delta=1,
            )

        with pytest.raises(JWTError, match="Invalid refresh token"):
            token_module.decode_refresh_token(token)
