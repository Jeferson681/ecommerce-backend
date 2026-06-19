"""JWT token utilities for authentication.

Security hardening (Phase 2):
- Claims: jti, iat, iss, aud added to both access and refresh tokens.
- Validation: issuer and audience verified on decode.

Phase 3:
- jti_hash() utility for storing token hash in DB (never the plain token).
"""

import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from backend.app.core.config import settings

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30")
)
JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))


def jti_hash(jti: str) -> str:
    """Return SHA-256 hex digest of a JWT jti claim.

    Used to store a hash of the refresh token's jti in the database
    so the plain token value is never persisted.
    """
    return hashlib.sha256(jti.encode()).hexdigest()


def _now() -> datetime:
    """Return current UTC datetime (overridable in tests)."""
    return datetime.now(UTC)


def _build_claims(data: dict[str, Any]) -> dict[str, Any]:
    """Add standard security claims to token payload.

    Inject jti, iat, iss, aud.
    """
    now = _now()
    claims = data.copy()
    claims.update(
        {
            "jti": uuid.uuid4().hex,
            "iat": now,
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        }
    )
    return claims


def create_access_token(data: dict[str, Any], expires_delta: int | None = None) -> str:
    """Create a JWT access token with the given payload and expiration.

    Parameters:
        data: Dictionary with claims to encode (typically contains user_id).
        expires_delta: Token expiration in minutes. Defaults to JWT_ACCESS_TOKEN_EXPIRES_MINUTES.

    Returns:
        JWT token as string.
    """
    to_encode = _build_claims(data)
    expire = _now() + timedelta(
        minutes=expires_delta or JWT_ACCESS_TOKEN_EXPIRES_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token, returning the payload.

    Parameters:
        token: JWT token string to decode.

    Returns:
        Decoded token payload (dictionary with claims).

    Raises:
        JWTError: If token is invalid, expired, or cannot be decoded.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}") from e


def create_refresh_token(data: dict[str, Any], expires_delta: int | None = None) -> str:
    """Create a refresh token for long-lived sessions.

    Parameters:
        data: Dictionary with claims (typically contains user_id).
        expires_delta: Token expiration in days. Defaults to JWT_REFRESH_TOKEN_EXPIRES_DAYS.

    Returns:
        JWT refresh token as string.
    """
    to_encode = _build_claims(data)
    to_encode.update({"type": "refresh"})
    expire = _now() + timedelta(days=expires_delta or JWT_REFRESH_TOKEN_EXPIRES_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
    )
    return encoded_jwt


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a refresh token.

    Parameters:
        token: JWT refresh token string to decode.

    Returns:
        Decoded token payload when valid.

    Raises:
        JWTError: If token is invalid, expired, or not a refresh token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
        if payload.get("type") != "refresh":
            raise JWTError("Token is not a refresh token")
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid refresh token: {str(e)}") from e
