"""User router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from backend.app.core.exceptions import InvalidPasswordError, Messages, NotFoundError
from backend.app.modules.auth.deps import get_current_user_id, require_admin
from backend.app.modules.user.schemas import (
    UserChangePassword,
    UserCreate,
    UserRead,
    UserUpdate,
)
from backend.app.modules.user.use_cases import (
    change_password as change_user_password,
    create_user as create_user_use_case,
    delete_user as delete_user_use_case,
    get_user as get_user_use_case,
    list_users as list_users_use_case,
    update_user as update_user_use_case,
)
from backend.app.uow.dependencies import get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_current_user_endpoint(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> UserRead:
    """Get the current authenticated user.

    Requires Bearer token in Authorization header.
    """
    return get_user_use_case(user_id, uow)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user_endpoint(
    user_data: UserCreate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> UserRead:
    try:
        return create_user_use_case(user_data, uow)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.EMAIL_ALREADY_EXISTS,
        ) from e


@router.get("/{user_id}", response_model=UserRead)
def get_user_endpoint(
    user_id: int,
    user_id_current: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> UserRead:
    """Return a specific user profile.

    Access: owner or admin (enforced in use case).
    """
    return get_user_use_case(user_id, uow, requesting_user_id=user_id_current)


@router.get("", response_model=list[UserRead])
def list_users_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _admin_id: Annotated[int, Depends(require_admin)],
) -> list[UserRead]:
    """List all users with pagination and filtering.

    Access: admin only (enforced by require_admin dependency).
    """
    return list_users_use_case(uow)


@router.patch("/{user_id}", response_model=UserRead)
def update_user_endpoint(
    user_id: int,
    user_data: UserUpdate,
    user_id_current: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> UserRead:
    """Update user profile data.

    Access: owner or admin (enforced in use case).
    """
    try:
        return update_user_use_case(
            user_id,
            user_data,
            uow,
            requesting_user_id=user_id_current,
        )

    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.EMAIL_ALREADY_EXISTS,
        ) from e


@router.patch(
    "/{user_id}/change-password",
    response_model=UserRead,
)
def change_password_endpoint(
    user_id: int,
    password_data: UserChangePassword,
    user_id_current: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> UserRead:
    """Change account password.

    Access: owner only (enforced in use case).
    """
    try:
        return change_user_password(
            user_id=user_id,
            new_password=password_data.new_password,
            uow=uow,
            requesting_user_id=user_id_current,
        )

    except (NotFoundError, InvalidPasswordError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_endpoint(
    user_id: int,
    user_id_current: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Delete or deactivate a user account.

    Access: owner or admin (enforced in use case).
    """
    delete_user_use_case(user_id, uow, requesting_user_id=user_id_current)
