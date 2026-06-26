"""Services related to carts."""

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.cart.domain.models import Cart, CartItem
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
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)
from backend.app.modules.product.services import get_product_or_raise
from backend.app.uow.unit_of_work import UnitOfWork


def get_cart(user_id: int, uow: UnitOfWork) -> CartRead:
    repository = CartRepository(uow.session)
    cart = get_cart_or_raise(repository, user_id)

    return CartRead.model_validate(cart)


def add_item(
    item_data: CartItemCreate,
    user_id: int,
    uow: UnitOfWork,
) -> CartItemRead:
    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    product_repository = ProductRepository(uow.session)

    product = get_product_or_raise(product_repository, item_data.product_id)

    if not product.is_active:
        raise ValidationError(Messages.PRODUCT_NOT_FOUND)

    try:
        cart = get_or_create_cart(cart_repository, user_id)

        cart_item = _upsert_cart_item(
            cart_item_repository=cart_item_repository,
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
        )

        uow.commit()

    except Exception:
        uow.rollback()
        raise

    return CartItemRead.model_validate(cart_item)


def update_item(
    item_id: int, item_data: CartItemUpdate, user_id: int, uow: UnitOfWork
) -> CartItemRead:
    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    cart = get_cart_or_raise(cart_repository, user_id)
    cart_item = get_cart_item_or_raise(cart_item_repository, cart.id, item_id)

    try:
        cart_item.quantity = item_data.quantity
        cart_item = cart_item_repository.update(cart_item)
        uow.commit()

    except Exception:
        uow.rollback()
        raise

    return CartItemRead.model_validate(cart_item)


def clear_cart(
    repository: CartRepository,
    cart: Cart,
) -> None:
    repository.delete(cart)


def remove_item(item_id: int, user_id: int, uow: UnitOfWork) -> None:
    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    cart = get_cart_or_raise(cart_repository, user_id)
    cart_item = get_cart_item_or_raise(cart_item_repository, cart.id, item_id)

    try:
        cart_item_repository.delete(cart_item)
        uow.commit()

    except Exception:
        uow.rollback()
        raise


def get_or_create_cart(repository: CartRepository, user_id: int) -> Cart:
    cart = repository.get_by_user_id(user_id)

    if cart is None:
        cart = repository.create(Cart(user_id=user_id))

    return cart


def get_cart_or_raise(repository: CartRepository, user_id: int) -> Cart:
    cart = repository.get_by_user_id(user_id)

    if cart is None:
        raise NotFoundError(Messages.CART_NOT_FOUND)

    return cart


def get_cart_item_or_raise(
    repository: CartItemRepository, cart_id: int, item_id: int
) -> CartItem:
    cart_item = repository.get_by_id(item_id)

    if cart_item is None or cart_item.cart_id != cart_id:
        raise NotFoundError(Messages.CART_ITEM_NOT_FOUND)

    return cart_item


def merge_cart_items(
    items: list[CartItemCreate],
    user_id: int,
    uow: UnitOfWork,
) -> CartRead:
    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    product_repository = ProductRepository(uow.session)

    for item in items:
        product = get_product_or_raise(product_repository, item.product_id)
        if not product.is_active:
            raise ValidationError(Messages.PRODUCT_NOT_FOUND)

    cart = get_or_create_cart(cart_repository, user_id)

    for item in items:
        _upsert_cart_item(
            cart_item_repository=cart_item_repository,
            cart_id=cart.id,
            product_id=item.product_id,
            quantity=item.quantity,
        )

    uow.commit()

    return CartRead.model_validate(cart)


def _upsert_cart_item(
    cart_item_repository: CartItemRepository,
    cart_id: int,
    product_id: int,
    quantity: int,
) -> CartItem:
    cart_item = cart_item_repository.get_by_cart_and_product(
        cart_id,
        product_id,
    )

    if cart_item is None:
        return cart_item_repository.create(
            CartItem(
                cart_id=cart_id,
                product_id=product_id,
                quantity=quantity,
            )
        )

    cart_item.quantity += quantity

    return cart_item_repository.update(cart_item)


def get_cart_items_or_raise(
    repository: CartItemRepository,
    cart_id: int,
) -> list[CartItem]:
    cart_items = repository.get_by_cart_id(cart_id)

    if not cart_items:
        raise ValidationError(Messages.ORDER_CART_EMPTY)

    return cart_items
