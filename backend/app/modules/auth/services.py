"""Services related to authentication."""

from datetime import UTC, datetime

from backend.app.core.exceptions import AuthenticationError, Messages
from backend.app.core.security import verify_password
from backend.app.modules.auth.domain.models import RefreshToken
from backend.app.modules.auth.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from backend.app.modules.auth.schemas import TokenResponse
from backend.app.modules.auth.tokens import (
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    jti_hash,
)
from backend.app.modules.user.repositories.user_repository import UserRepository
from backend.app.uow.unit_of_work import UnitOfWork


def login(email: str, password: str, uow: UnitOfWork) -> TokenResponse:
    user_repo = UserRepository(uow.session)
    user = user_repo.get_by_email(email)
    if not user:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)
    if not verify_password(password, user.password_hash):
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    payload = decode_refresh_token(refresh_token)
    expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
    token_repo = RefreshTokenRepository(uow.session)
    token_record = RefreshToken(
        jti_hash=jti_hash(payload["jti"]),
        user_id=user.id,
        expires_at=expires_at,
    )
    token_repo.create(token_record)
    uow.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",  # nosec B106
        expires_in=JWT_ACCESS_TOKEN_EXPIRES_MINUTES * 60,
    )


def logout(refresh_token_str: str, uow: UnitOfWork) -> None:
    try:
        payload = decode_refresh_token(refresh_token_str)
    except Exception as e:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID) from e
    token_repo = RefreshTokenRepository(uow.session)
    record = token_repo.get_by_jti_hash(jti_hash(payload["jti"]))
    if record is None:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)
    if record.revoked:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)
    token_repo.revoke(record.id)
    uow.commit()


def refresh_access_token(refresh_token_str: str, uow: UnitOfWork) -> TokenResponse:
    try:
        payload = decode_refresh_token(refresh_token_str)
    except Exception as e:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID) from e
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)
    token_repo = RefreshTokenRepository(uow.session)
    record = token_repo.get_by_jti_hash(jti_hash(payload["jti"]))
    if record is None:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)
    if record.revoked:
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)
    token_repo.revoke(record.id)
    new_access_token = create_access_token(data={"sub": str(user_id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user_id)})
    new_payload = decode_refresh_token(new_refresh_token)
    new_expires_at = datetime.fromtimestamp(new_payload["exp"], tz=UTC)
    new_record = RefreshToken(
        jti_hash=jti_hash(new_payload["jti"]),
        user_id=int(user_id),
        expires_at=new_expires_at,
    )
    token_repo.create(new_record)
    uow.commit()
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",  # nosec B106
        expires_in=JWT_ACCESS_TOKEN_EXPIRES_MINUTES * 60,
    )
