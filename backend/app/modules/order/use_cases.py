"""Order use cases.

Responsibility: coordinate checkout and order retrieval workflows.
"""

from backend.app.core.exceptions import Messages, NotFoundError
from backend.app.idempotency.helpers import persist_idempotency_response, try_replay
from backend.app.idempotency.repositories.idempotency_repository import (
    IdempotencyRepository,
)
from backend.app.modules.cart.domain.models import CartItem
from backend.app.modules.order.domain.models import Order, OrderItem
from backend.app.modules.order.repositories.order_repository import (
    OrderItemRepository,
    OrderRepository,
)
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.repositories.user_repository import UserRepository
from backend.app.modules.user.use_cases import is_admin
from backend.app.uow.unit_of_work import UnitOfWork


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

    if not is_owner:
        if requesting_user_id is None:
            raise NotFoundError(Messages.ORDER_NOT_FOUND)
        user_repository = UserRepository(uow.session)
        if not is_admin(user_repository, requesting_user_id):
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


def get_order_or_raise(
    repository: OrderRepository,
    order_id: int,
) -> Order:
    order = repository.get_by_id(order_id)

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return order


def persist_idempotent_response_if_needed(
    repository: IdempotencyRepository,
    order: Order,
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
    repository: IdempotencyRepository,
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
