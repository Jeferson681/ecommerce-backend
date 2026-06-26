"""Authentication endpoints (scaffolds).

These endpoints are defined with their request/response signatures but are
intentionally left unimplemented (bodies contain `pass`).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError

from backend.app.core.rate_limit import limiter
from backend.app.modules.auth import (
    schemas as auth_schemas,
    services as auth_use_cases,
)
from backend.app.modules.auth.deps import get_current_user_id
from backend.app.uow.dependencies import get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=auth_schemas.TokenResponse)
@limiter.limit("5/minute")
def token_endpoint(
    request: Request,
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
    return auth_use_cases.login(
        email=payload.email,
        password=payload.password,
        uow=uow,
    )


@router.post("/logout", status_code=204)
def logout_endpoint(
    refresh: auth_schemas.RefreshTokenRequest,
    _user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Revoke refresh token / logout user.

    Parameters
    - refresh: payload containing refresh token
    - uow: UnitOfWork dependency for repository access

    Raises:
    - JWTError: Invalid or expired refresh token
    """
    try:
        auth_use_cases.logout(
            refresh_token_str=refresh.refresh_token,
            uow=uow,
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from e


@router.post("/refresh", response_model=auth_schemas.TokenResponse)
@limiter.limit("10/minute")
def refresh_endpoint(
    request: Request,
    refresh: auth_schemas.RefreshTokenRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> auth_schemas.TokenResponse:
    """Exchange refresh token for new access + refresh token pair.

    Parameters:
        refresh: RefreshTokenRequest containing refresh_token
        uow: UnitOfWork dependency for repository access

    Returns:
        TokenResponse with new access_token and new refresh_token

    Raises:
        AuthenticationError: Invalid or expired refresh token
    """
    return auth_use_cases.refresh_access_token(
        refresh_token_str=refresh.refresh_token,
        uow=uow,
    )
