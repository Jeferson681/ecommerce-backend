"""Dependency functions for authentication-related operations."""

from typing import Annotated

from fastapi import Header, HTTPException, status
from jose import JWTError

from backend.app.modules.auth.tokens import decode_access_token


def get_current_user_id(authorization: Annotated[str | None, Header()] = None) -> int:
    """Extract and validate user ID from JWT Bearer token.

    Parameters:
        authorization: Authorization header value (typically "Bearer <token>").

    Returns:
        User ID from token payload.

    Raises:
        HTTPException: Invalid/missing token (401).
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header.",
        )

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format.",
        )

    token = parts[1]

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )
        return int(user_id)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from e
