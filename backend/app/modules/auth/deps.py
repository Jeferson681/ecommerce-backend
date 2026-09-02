"""Dependency functions for authentication-related operations."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from jose.exceptions import ExpiredSignatureError

from backend.app.modules.auth.tokens import decode_access_token
from backend.app.modules.user.repositories.user_repository import UserRepository
from backend.app.modules.user.services import is_admin
from backend.app.uow.dependencies import get_uow
from backend.app.uow.unit_of_work import UnitOfWork


def get_current_user_id(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    authorization: Annotated[str | None, Header()] = None,
) -> int:
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
        current_user_id = int(user_id)
        user = UserRepository(uow.session).get_by_id(current_user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive user.",
            )
        return current_user_id
    except ExpiredSignatureError as e:
        # RFC 6750 signal: lets clients distinguish an expired access token
        # (refresh flow applies) from other 401 authentication failures.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={
                "WWW-Authenticate": (
                    'Bearer error="invalid_token", '
                    'error_description="The access token has expired"'
                )
            },
        ) from e
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from e


def require_admin(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> int:
    """Require the authenticated user to be an admin.

    Queries the database to check the user's role.

    Returns:
        The admin user ID.

    Raises:
        HTTPException: 403 if the user is not an admin.
    """
    repository = UserRepository(uow.session)

    if not is_admin(repository, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return user_id
