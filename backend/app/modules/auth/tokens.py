"""JWT token utilities for authentication."""

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30")
)
JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))


def create_access_token(data: dict[str, Any], expires_delta: int | None = None) -> str:
    """Create a JWT access token with the given payload and expiration.

    Parameters:
        data: Dictionary with claims to encode (typically contains user_id).
        expires_delta: Token expiration in minutes. Defaults to JWT_ACCESS_TOKEN_EXPIRES_MINUTES.

    Returns:
        JWT token as string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_delta or JWT_ACCESS_TOKEN_EXPIRES_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
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
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
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
    to_encode = data.copy()
    to_encode.update({"type": "refresh"})
    expire = datetime.now(UTC) + timedelta(
        days=expires_delta or JWT_REFRESH_TOKEN_EXPIRES_DAYS
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
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
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Token is not a refresh token")
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid refresh token: {str(e)}") from e
