"""Services for User management."""

from backend.app.core.exceptions import (
    AuthenticationError,
    EmailAlreadyExistsError,
    InvalidPasswordError,
    Messages,
    NotFoundError,
)
from backend.app.core.security import (
    hash_password,
    validate_password_policy,
    verify_password,
)
from backend.app.modules.user.domain.models import User, UserRole
from backend.app.modules.user.repositories.user_repository import UserRepository
from backend.app.modules.user.schemas import UserCreate, UserRead, UserUpdate
from backend.app.uow.unit_of_work import UnitOfWork


def get_user_or_raise(repository: UserRepository, user_id: int) -> User:
    """Retrieve a user or raise NotFoundError if it doesn't exist."""
    user = repository.get_by_id(user_id)
    if not user:
        raise NotFoundError(Messages.USER_NOT_FOUND)
    return user


def is_admin(repository: UserRepository, user_id: int) -> bool:
    user = repository.get_by_id(user_id)

    if user is None:
        return False

    return user.role == UserRole.ADMIN


def create_user(
    user_data: UserCreate,
    uow: UnitOfWork,
) -> UserRead:
    if not validate_password_policy(user_data.password):
        raise InvalidPasswordError(Messages.INVALID_CREDENTIAL_POLICY)

    repository = UserRepository(uow.session)

    if repository.get_by_email(user_data.email) is not None:
        raise EmailAlreadyExistsError(Messages.EMAIL_ALREADY_EXISTS)

    user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )

    try:
        repository.create(user)
        uow.commit()

    except Exception:
        uow.rollback()
        raise

    return UserRead.model_validate(user)


def get_user(
    user_id: int,
    uow: UnitOfWork,
    requesting_user_id: int | None = None,
) -> UserRead:
    """Get a user by ID.

    Access: owner or admin.
    When `requesting_user_id` is provided, only the owner or an admin can access.
    """
    repository = UserRepository(uow.session)
    user = get_user_or_raise(repository, user_id)

    if requesting_user_id is not None:
        _check_owner_or_admin(repository, user_id, requesting_user_id)

    return UserRead.model_validate(user)


def list_users(
    uow: UnitOfWork,
    limit: int = 20,
    offset: int = 0,
) -> list[UserRead]:
    repository = UserRepository(uow.session)
    users = repository.list(limit=limit, offset=offset)

    return [UserRead.model_validate(user) for user in users]


def update_user(
    user_id: int,
    user_data: UserUpdate,
    uow: UnitOfWork,
    requesting_user_id: int | None = None,
) -> UserRead:
    """Update a user profile.

    Access: owner or admin.
    When `requesting_user_id` is provided, only the owner or an admin can update.
    """
    repository = UserRepository(uow.session)
    user = get_user_or_raise(repository, user_id)

    if requesting_user_id is not None:
        _check_owner_or_admin(repository, user_id, requesting_user_id)

    for key, value in user_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(user, key, value)

    try:
        uow.commit()

    except Exception:
        uow.rollback()
        raise

    return UserRead.model_validate(user)


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    uow: UnitOfWork,
    requesting_user_id: int | None = None,
) -> UserRead:
    """Change account password.

    Access: owner only.
    When `requesting_user_id` is provided, only the owner can change the password.
    """
    repository = UserRepository(uow.session)
    user = get_user_or_raise(repository, user_id)

    if requesting_user_id is not None and requesting_user_id != user_id:
        raise NotFoundError(Messages.USER_NOT_FOUND)

    if not verify_password(current_password, user.password_hash):
        raise AuthenticationError(Messages.EMAIL_OR_PASSWORD_INVALID)

    if not validate_password_policy(new_password):
        raise InvalidPasswordError(Messages.INVALID_CREDENTIAL_POLICY)

    user.password_hash = hash_password(new_password)

    try:
        uow.commit()

    except Exception:
        uow.rollback()
        raise

    return UserRead.model_validate(user)


def delete_user(
    user_id: int,
    uow: UnitOfWork,
    requesting_user_id: int | None = None,
) -> None:
    """Delete a user account.

    Access: owner or admin.
    When `requesting_user_id` is provided, only the owner or an admin can delete.
    """
    repository = UserRepository(uow.session)
    user = get_user_or_raise(repository, user_id)

    if requesting_user_id is not None:
        _check_owner_or_admin(repository, user_id, requesting_user_id)

    try:
        repository.delete(user)
        uow.commit()

    except Exception:
        uow.rollback()
        raise


def _check_owner_or_admin(
    repository: UserRepository,
    target_user_id: int,
    requesting_user_id: int,
) -> None:
    """Raise NotFoundError if the requesting user is neither the owner nor an admin."""
    if requesting_user_id == target_user_id:
        return

    if not is_admin(repository, requesting_user_id):
        raise NotFoundError(Messages.USER_NOT_FOUND)
