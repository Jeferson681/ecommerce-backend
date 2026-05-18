"""Use cases for User management."""

from app.application.uow.unit_of_work import UnitOfWork
from app.core.exceptions import InvalidPasswordError, Messages, NotFoundError
from app.modules.auth.security import hash_password
from app.modules.auth.validators import validate_password_policy
from app.modules.user.domain.models import User
from app.modules.user.repositories.user_repository import UserRepository
from app.modules.user.schemas import UserCreate, UserRead, UserUpdate


def create_user(
    user_data: UserCreate,
    uow: UnitOfWork,
) -> UserRead:
    if not validate_password_policy(user_data.password):
        raise InvalidPasswordError(Messages.INVALID_CREDENTIAL_POLICY)

    repository = UserRepository(uow.session)

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
) -> UserRead:
    repository = UserRepository(uow.session)
    user = repository.get_by_id(user_id)

    if not user:
        raise NotFoundError(Messages.USER_NOT_FOUND)

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
) -> UserRead:
    repository = UserRepository(uow.session)
    user = repository.get_by_id(user_id)

    if not user:
        raise NotFoundError(Messages.USER_NOT_FOUND)

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
    new_password: str,
    uow: UnitOfWork,
) -> UserRead:
    repository = UserRepository(uow.session)
    user = repository.get_by_id(user_id)

    if not user:
        raise NotFoundError(Messages.USER_NOT_FOUND)

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
) -> None:
    repository = UserRepository(uow.session)
    user = repository.get_by_id(user_id)

    if not user:
        raise NotFoundError(Messages.USER_NOT_FOUND)

    try:
        repository.delete(user)
        uow.commit()

    except Exception:
        uow.rollback()
        raise


def restore_user(
    *args: object,
    **kwargs: object,
) -> None:
    raise NotImplementedError("user.use_cases.restore_user " "is not implemented")
