"""Cart API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.app.modules.auth.deps import get_current_user_id
from backend.app.modules.cart.schemas import (
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
)
from backend.app.modules.cart.services import (
    add_item,
    clear_user_cart,
    get_cart,
    merge_cart_items,
    remove_item,
    update_item,
)
from backend.app.uow.dependencies import get_uow
from backend.app.uow.unit_of_work import UnitOfWork

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartRead)
def get_cart_endpoint(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> CartRead:
    return get_cart(user_id, uow)


@router.post(
    "/items",
    response_model=CartItemRead,
    status_code=status.HTTP_201_CREATED,
)
def add_item_endpoint(
    item_data: CartItemCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> CartItemRead:
    return add_item(item_data, user_id, uow)


@router.patch("/items/{item_id}", response_model=CartItemRead)
def update_item_endpoint(
    item_id: int,
    item_data: CartItemUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> CartItemRead:
    return update_item(item_id, item_data, user_id, uow)


@router.delete("/items/{item_id}", status_code=204)
def remove_item_endpoint(
    item_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    remove_item(item_id, user_id, uow)


@router.delete("", status_code=204)
def clear_cart_endpoint(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Remove the current user's cart together with all of its items."""
    clear_user_cart(user_id, uow)


@router.post("/merge", response_model=CartRead)
def merge_cart_endpoint(
    items: list[CartItemCreate],
    user_id: Annotated[int, Depends(get_current_user_id)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> CartRead:
    return merge_cart_items(items, user_id, uow)
