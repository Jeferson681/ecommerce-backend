"""Use cases for authentication."""

from app.application.uow.unit_of_work import UnitOfWork
from app.core.exceptions import AuthenticationError, Messages
from app.modules.auth.schemas import TokenResponse
from app.modules.auth.security import verify_password
from app.modules.auth.tokens import (
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.modules.user.repositories.user_repository import UserRepository


def login(email: str, password: str, uow: UnitOfWork) -> TokenResponse:
    """Authenticate a user and return token information.

    Parameters:
        email: User email address.
        password: Plain text password to validate.
        uow: UnitOfWork instance for repository access.

    Returns:
        TokenResponse with access_token, refresh_token, token_type, and expires_in.

    Raises:
        AuthenticationError: Invalid email or password.
    """
    repository = UserRepository(uow.session)
    user = repository.get_by_email(email)

    if not user:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)

    if not verify_password(password, user.password_hash):
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",  # nosec B106 - string literal, not a password
        expires_in=JWT_ACCESS_TOKEN_EXPIRES_MINUTES * 60,
    )


def logout(refresh_token: str, uow: UnitOfWork) -> None:
    """Revoke or validate a refresh token during logout.

    Parameters:
        refresh_token: Refresh token to revoke.
        uow: UnitOfWork instance reserved for future persistence/blacklist support.

    Returns:
        None
    """
    del uow
    decode_refresh_token(refresh_token)


def refresh_access_token(refresh_token: str, uow: UnitOfWork) -> TokenResponse:
    """Exchange a valid refresh token for a new access token.

    Parameters:
        refresh_token: Refresh token to validate and exchange.
        uow: UnitOfWork instance for repository access.

    Returns:
        TokenResponse with new access_token and same refresh_token.

    Raises:
        AuthenticationError: Invalid or expired refresh token.
    """
    del uow  # Reserved for future blacklist/revocation support

    try:
        payload = decode_refresh_token(refresh_token)
    except Exception as e:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID) from e

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)

    # Generate new access token with same user_id
    access_token = create_access_token(data={"sub": user_id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Return the same refresh token
        token_type="bearer",  # nosec B106 - string literal, not a password
        expires_in=JWT_ACCESS_TOKEN_EXPIRES_MINUTES * 60,
    )
