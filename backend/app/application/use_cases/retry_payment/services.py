"""Retry Payment services.
Responsibility: provide reusable operations for checkout workflows
"""

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.order.domain.models import Order, OrderStatus
from backend.app.modules.order.repositories.order_repository import (
    OrderRepository,
)
from backend.app.modules.payment.domain.models import Payment, PaymentStatus
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)


def get_failed_payment_for_order(
    payment_repository: PaymentRepository,
    *,
    order_id: int,
) -> Payment | None:
    payments = payment_repository.get_by_order_id(order_id)

    if not payments:
        return None

    for payment in payments:
        if payment.status == PaymentStatus.FAILED:
            return payment

    return None


def get_order_pending(
    order_repository: OrderRepository,
    *,
    user_id: int,
) -> Order | None:
    orders = order_repository.get_by_user_id(user_id)

    if not orders:
        return None

    for order in orders:
        if order.status == OrderStatus.PENDING:
            return order

    return None


def get_pending_order_and_failed_payment(
    order_repository: OrderRepository,
    payment_repository: PaymentRepository,
    *,
    user_id: int,
) -> tuple[Order, Payment]:
    order = get_order_pending(
        order_repository,
        user_id=user_id,
    )

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)
    payment = get_failed_payment_for_order(
        payment_repository,
        order_id=order.id,
    )

    if payment is None:
        raise ValidationError(Messages.NO_FAILED_PAYMENT_FOUND)

    return order, payment
