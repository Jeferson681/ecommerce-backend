"""Services related to orders."""

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.idempotency.helpers import persist_idempotency_response, try_replay
from backend.app.modules.cart.domain.models import CartItem
from backend.app.modules.order.domain.models import Order, OrderItem, OrderStatus
from backend.app.modules.order.repositories.order_repository import (
    OrderItemRepository,
    OrderRepository,
)
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.product.domain.models import Product
from backend.app.uow.unit_of_work import UnitOfWork


def get_order_or_raise(
    order_repository: OrderRepository,
    order_id: int,
) -> Order:
    """Retrieve an order or raise NotFoundError if it doesn't exist."""
    order = order_repository.get_by_id(order_id)
    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)
    return order


def get_order(
    order_id: int,
    user_id: int,
    uow: UnitOfWork,
) -> OrderRead:
    """Retrieve a single order by ID.

    Access: owner only.
    Admin access is handled by the caller when needed.
    """

    repository = OrderRepository(uow.session)

    order = get_order_or_raise(repository, order_id)

    if order.user_id != user_id:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return OrderRead.model_validate(order)


def list_orders(user_id: int, uow: UnitOfWork) -> list[OrderRead]:
    """List all orders for the authenticated user."""

    repository = OrderRepository(uow.session)

    orders = repository.get_by_user_id(user_id)

    return [OrderRead.model_validate(order) for order in orders]


def create_order_from_cart(
    cart_items: list[CartItem],
    product_map: dict[int, Product],
    order_repository: OrderRepository,
    order_item_repository: OrderItemRepository,
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

    return order


def persist_idempotent_response_if_needed(
    repository,
    order,
    idempotency_key: str | None,
    user_id: int,
) -> None:
    if idempotency_key is None:
        return

    response_json = OrderRead.model_validate(order).model_dump_json()

    persist_idempotency_response(
        repository=repository,
        idempotency_key=idempotency_key,
        user_id=user_id,
        status=201,
        body=response_json,
    )


def try_order_response_replay(
    repository,
    idempotency_key: str | None,
    user_id: int,
) -> OrderRead | None:
    if idempotency_key is None:
        return None

    raw = try_replay(
        repository=repository,
        idempotency_key=idempotency_key,
        user_id=user_id,
    )

    if raw is None:
        return None

    return OrderRead.model_validate(raw)


def get_pending_order_for_user(
    order_repository: OrderRepository,
    *,
    order_id: int,
    user_id: int,
) -> Order:
    order = get_order_or_raise(order_repository, order_id)

    if order.user_id != user_id:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    if order.status != OrderStatus.PENDING:
        raise ValidationError(Messages.ORDER_IS_NOT_PENDING)

    return order


def get_order_for_user(
    order_repository: OrderRepository,
    *,
    order_id: int,
    user_id: int,
) -> Order:
    order = get_order_or_raise(order_repository, order_id)

    if order.user_id != user_id:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return order
