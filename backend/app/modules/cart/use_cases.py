"""Cart use cases."""

from sqlalchemy.exc import IntegrityError

from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.exceptions import Messages, NotFoundError
from backend.app.modules.cart.domain.models import Cart
from backend.app.modules.cart.repositories.cart_repository import (
    CartItemRepository,
    CartRepository,
)
from backend.app.modules.cart.schemas import (
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
)


def get_cart(user_id: int, uow: UnitOfWork) -> CartRead:
    """Get the user's cart, creating it when needed."""
    cart_repository = CartRepository(uow.session)
    cart = cart_repository.get_by_user_id(user_id)

    if cart is None:
        cart = cart_repository.create(Cart(user_id=user_id))
        uow.commit()

    return CartRead.model_validate(cart)


def add_item(item_data: CartItemCreate, user_id: int, uow: UnitOfWork) -> CartItemRead:
    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)

    try:
        cart = cart_repository.get_or_create_by_user(user_id)
        cart_item = cart_item_repository.add_or_increment(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
        )
        uow.commit()

    except IntegrityError:
        uow.rollback()
        cart = cart_repository.get_or_create_by_user(user_id)
        existing_cart_item = cart_item_repository.get_by_cart_and_product(
            cart.id, item_data.product_id
        )

        if existing_cart_item is None:
            cart_item = cart_item_repository.add_or_increment(
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
            )
        else:
            existing_cart_item.quantity += item_data.quantity
            cart_item = cart_item_repository.update(existing_cart_item)

        uow.commit()

    except Exception:
        uow.rollback()
        raise

    return CartItemRead.model_validate(cart_item)


def update_item(
    item_id: int, item_data: CartItemUpdate, user_id: int, uow: UnitOfWork
) -> CartItemRead:
    """Update the quantity of an item in the user's cart."""
    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    cart = cart_repository.get_by_user_id(user_id)

    if cart is None:
        raise NotFoundError(Messages.CART_NOT_FOUND)

    cart_item = cart_item_repository.get_by_id(item_id)

    if cart_item is None or cart_item.cart_id != cart.id:
        raise NotFoundError(Messages.CART_ITEM_NOT_FOUND)

    try:
        cart_item.quantity = item_data.quantity
        cart_item = cart_item_repository.update(cart_item)
        uow.commit()

    except Exception:
        uow.rollback()
        raise

    return CartItemRead.model_validate(cart_item)


def remove_item(item_id: int, user_id: int, uow: UnitOfWork) -> None:
    """Remove an item from the user's cart."""
    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    cart = cart_repository.get_by_user_id(user_id)

    if cart is None:
        raise NotFoundError(Messages.CART_NOT_FOUND)

    cart_item = cart_item_repository.get_by_id(item_id)

    if cart_item is None or cart_item.cart_id != cart.id:
        raise NotFoundError(Messages.CART_ITEM_NOT_FOUND)

    try:
        cart_item_repository.delete(cart_item)
        uow.commit()

    except Exception:
        uow.rollback()
        raise
