"""Order use cases.

Responsibility: coordinate checkout and order retrieval workflows.
"""

from backend.app.core.exceptions import Messages, NotFoundError
from backend.app.modules.order.domain.models import Order
from backend.app.modules.order.repositories.order_repository import (
    OrderRepository,
)
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.user.repositories.user_repository import UserRepository
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


def get_order_or_raise(
    repository: OrderRepository,
    order_id: int,
) -> Order:
    order = repository.get_by_id(order_id)

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return order
