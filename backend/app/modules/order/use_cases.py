"""Order use cases.

Responsibility: coordinate checkout and order retrieval workflows.
"""

import hashlib

from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.idempotency.helpers import (
    persist_idempotency_response,
    reserve_idempotency_key,
    try_replay,
)
from backend.app.idempotency.repositories import IdempotencyRepository
from backend.app.modules.cart.domain.models import Cart, CartItem
from backend.app.modules.cart.repositories.cart_repository import (
    CartItemRepository,
    CartRepository,
)
from backend.app.modules.order.domain.models import Order, OrderItem
from backend.app.modules.order.repositories.order_repository import (
    OrderItemRepository,
    OrderRepository,
)
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.payment.schemas import PaymentCreate
from backend.app.modules.payment.use_cases import (
    process_payment as process_payment_use_case,
)
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)
from backend.app.modules.user.repositories.user_repository import UserRepository


def checkout(
    user_id: int,
    uow: UnitOfWork,
    idempotency_key: str | None = None,
    request_hash: str | None = None,
) -> OrderRead:
    """Complete checkout for the authenticated user."""

    _validate_idempotency_input(idempotency_key, request_hash)

    cart_repository = CartRepository(uow.session)
    cart_item_repository = CartItemRepository(uow.session)
    product_repository = ProductRepository(uow.session)
    order_repository = OrderRepository(uow.session)
    order_item_repository = OrderItemRepository(uow.session)
    idempotency_repository = IdempotencyRepository(uow.session)

    replay = _try_replay_if_possible(
        repository=idempotency_repository,
        idempotency_key=idempotency_key,
        user_id=user_id,
    )

    if replay is not None:
        return replay

    try:
        cart = _get_cart_or_raise(cart_repository, user_id)

        cart_items = _get_cart_items_or_raise(
            cart_item_repository,
            cart.id,
        )

        product_map = _validate_stock_and_build_product_map(
            cart_items,
            product_repository,
        )

        _reserve_idempotency_if_needed(
            repository=idempotency_repository,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            user_id=user_id,
        )

        order = _create_order_from_cart(
            cart_items=cart_items,
            product_map=product_map,
            order_repository=order_repository,
            order_item_repository=order_item_repository,
            product_repository=product_repository,
            user_id=user_id,
        )

        _clear_cart(cart_repository, cart)

        payment_request_hash = hashlib.sha256()
        payment_request_hash.update(f"order:{order.id}".encode())
        payment_request_hash.update(f"user:{user_id}".encode())
        payment_request_hash.update(
            f"amount:{sum(product_map[item.product_id].price * item.quantity for item in cart_items)}".encode()
        )

        process_payment_use_case(
            PaymentCreate(order_id=order.id),
            uow,
            requesting_user_id=user_id,
            idempotency_key=f"{idempotency_key}:payment" if idempotency_key else None,
            request_hash=payment_request_hash.hexdigest() if idempotency_key else None,
            commit=False,
        )

        uow.flush()

        _persist_idempotent_response_if_needed(
            repository=idempotency_repository,
            order_repository=order_repository,
            order_id=order.id,
            idempotency_key=idempotency_key,
            user_id=user_id,
        )

        uow.commit()

    except Exception:
        uow.rollback()
        raise

    refreshed = _get_order_or_raise(order_repository, order.id)

    return OrderRead.model_validate(refreshed)


def get_order(
    order_id: int,
    user_id: int,
    uow: UnitOfWork,
    requesting_user_id: int | None = None,
) -> OrderRead:
    """Retrieve a single order by ID."""

    repository = OrderRepository(uow.session)

    order = repository.get_by_id(order_id)

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    is_owner = order.user_id == user_id
    is_admin = False

    if not is_owner and requesting_user_id is not None:
        user_repository = UserRepository(uow.session)

        requester = user_repository.get_by_id(requesting_user_id)

        is_admin = requester is not None and requester.role == "admin"

    if not is_owner and not is_admin:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return OrderRead.model_validate(order)


def list_orders(user_id: int, uow: UnitOfWork) -> list[OrderRead]:
    """List all orders for the authenticated user."""

    repository = OrderRepository(uow.session)

    orders = repository.get_by_user_id(user_id)

    return [OrderRead.model_validate(order) for order in orders]


def _validate_idempotency_input(
    idempotency_key: str | None,
    request_hash: str | None,
) -> None:
    if bool(idempotency_key) != bool(request_hash):
        raise ValidationError(
            "Both idempotency_key and request_hash must be provided together."
        )


def _try_replay_if_possible(
    repository: IdempotencyRepository,
    idempotency_key: str | None,
    user_id: int,
) -> OrderRead | None:
    if idempotency_key is None:
        return None

    return try_replay(
        repository=repository,
        key=idempotency_key,
        model_cls=OrderRead,
        user_id=user_id,
    )


def _reserve_idempotency_if_needed(
    repository: IdempotencyRepository,
    idempotency_key: str | None,
    request_hash: str | None,
    user_id: int,
) -> None:
    if idempotency_key is None or request_hash is None:
        return

    reserve_idempotency_key(
        repository=repository,
        key=idempotency_key,
        user_id=user_id,
        request_hash=request_hash,
    )


def _get_cart_or_raise(
    repository: CartRepository,
    user_id: int,
) -> Cart:
    cart = repository.get_by_user_id(user_id)

    if cart is None:
        raise NotFoundError(Messages.CART_NOT_FOUND)

    return cart


def _get_cart_items_or_raise(
    repository: CartItemRepository,
    cart_id: int,
) -> list[CartItem]:
    cart_items = repository.get_by_cart_id(cart_id)

    if not cart_items:
        raise ValidationError(Messages.ORDER_CART_EMPTY)

    return cart_items


def _validate_stock_and_build_product_map(
    cart_items: list[CartItem],
    repository: ProductRepository,
) -> dict[int, Product]:
    product_map: dict[int, Product] = {}

    for cart_item in cart_items:
        product = repository.get_by_id(cart_item.product_id)

        if product is None:
            raise NotFoundError(Messages.PRODUCT_NOT_FOUND)

        if product.stock_quantity < cart_item.quantity:
            raise ValidationError(
                f"{Messages.ORDER_INSUFFICIENT_STOCK} "
                f"(product_id={cart_item.product_id})"
            )

        product_map[cart_item.product_id] = product

    return product_map


def _create_order_from_cart(
    cart_items: list[CartItem],
    product_map: dict[int, Product],
    order_repository: OrderRepository,
    order_item_repository: OrderItemRepository,
    product_repository: ProductRepository,
    user_id: int,
) -> Order:
    order = order_repository.create(Order(user_id=user_id))

    for cart_item in cart_items:
        product = product_map[cart_item.product_id]

        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=product.price,
        )

        order.items.append(order_item)
        order_item_repository.create(order_item)

        success = product_repository.decrement_stock_if_enough(
            product.id,
            cart_item.quantity,
        )

        if not success:
            raise ValidationError(
                f"{Messages.ORDER_INSUFFICIENT_STOCK} "
                f"(product_id={cart_item.product_id})"
            )

    return order


def _clear_cart(
    repository: CartRepository,
    cart: Cart,
) -> None:
    repository.delete(cart)


def _persist_idempotent_response_if_needed(
    repository: IdempotencyRepository,
    order_repository: OrderRepository,
    order_id: int,
    idempotency_key: str | None,
    user_id: int,
) -> None:
    if idempotency_key is None:
        return

    order = _get_order_or_raise(order_repository, order_id)

    response_json = OrderRead.model_validate(order).model_dump_json()

    persist_idempotency_response(
        repository=repository,
        key=idempotency_key,
        user_id=user_id,
        status=201,
        body=response_json,
    )


def _get_order_or_raise(
    repository: OrderRepository,
    order_id: int,
) -> Order:
    order = repository.get_by_id(order_id)

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return order
