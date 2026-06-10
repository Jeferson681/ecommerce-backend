"""Order use cases.

Responsibility: coordinate checkout and order retrieval workflows.
"""

from backend.app.core.exceptions import Messages, NotFoundError
from backend.app.idempotency.helpers import persist_idempotency_response, try_replay
from backend.app.idempotency.repositories.idempotency_repository import (
    IdempotencyRepository,
)
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


def persist_idempotent_response_if_needed(
    repository: IdempotencyRepository,
    order_repository: OrderRepository,
    order_id: int,
    idempotency_key: str | None,
    user_id: int,
) -> None:
    if idempotency_key is None:
        return

    order = get_order_or_raise(order_repository, order_id)

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
