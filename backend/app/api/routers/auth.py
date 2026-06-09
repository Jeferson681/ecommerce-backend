"""Authentication endpoints (scaffolds).

These endpoints are defined with their request/response signatures but are
intentionally left unimplemented (bodies contain `pass`).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError

from backend.app.core.exceptions import AuthenticationError
from backend.app.modules.auth import (
    schemas as auth_schemas,
    use_cases as auth_use_cases,
)
from backend.app.modules.auth.deps import get_current_user_id
from backend.app.modules.user import (
    schemas as user_schemas,
    use_cases as user_use_cases,
)
from backend.app.uow.dependencies import get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=auth_schemas.TokenResponse)
def token_endpoint(
    payload: auth_schemas.LoginRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> auth_schemas.TokenResponse:
    """Authenticate user and return access + refresh tokens.

    Parameters
    - payload: `LoginRequest` containing email and password
    - uow: UnitOfWork dependency for repository access

    Returns: TokenResponse with access_token, refresh_token, token_type, expires_in

    Raises:
    - AuthenticationError: Invalid credentials
    """
    try:
        return auth_use_cases.login(
            email=payload.email,
            password=payload.password,
            uow=uow,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.post("/logout", status_code=204)
def logout_endpoint(
    refresh: auth_schemas.RefreshTokenRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _user_id: Annotated[int, Depends(get_current_user_id)],
) -> None:
    """Revoke refresh token / logout user.

    Parameters
    - refresh: payload containing refresh token
    - uow: UnitOfWork dependency

    Raises:
    - JWTError: Invalid or expired refresh token
    """
    try:
        auth_use_cases.logout(
            refresh_token=refresh.refresh_token,
            uow=uow,
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from e


@router.post("/refresh", response_model=auth_schemas.TokenResponse)
def refresh_endpoint(
    refresh: auth_schemas.RefreshTokenRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> auth_schemas.TokenResponse:
    """Exchange refresh token for new access token.

    Parameters:
        refresh: RefreshTokenRequest containing refresh_token
        uow: UnitOfWork dependency for repository access

    Returns:
        TokenResponse with new access_token and same refresh_token

    Raises:
        AuthenticationError: Invalid or expired refresh token
    """
    try:
        return auth_use_cases.refresh_access_token(
            refresh_token=refresh.refresh_token,
            uow=uow,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.get("/session", response_model=user_schemas.UserRead)
def session_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user_id: Annotated[int, Depends(get_current_user_id)],
) -> user_schemas.UserRead:
    """Return the current authenticated user's session/profile.

    Uses the same access rules as `get_user` (owner or admin). Returns
    the `UserRead` schema for the authenticated user.
    """
    return user_use_cases.get_user(user_id=user_id, uow=uow, requesting_user_id=user_id)
