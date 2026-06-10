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


def get_pending_order_and_failed_payment(
    order_repository: OrderRepository,
    payment_repository: PaymentRepository,
    *,
    order_id: int,
    user_id: int,
) -> tuple[Order, Payment]:
    order = order_repository.get_by_id(order_id)

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    if order.user_id != user_id:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    if order.status != OrderStatus.PENDING:
        raise ValidationError(Messages.ORDER_IS_NOT_PENDING)

    payment = get_failed_payment_for_order(
        payment_repository,
        order_id=order.id,
    )

    if payment is None:
        raise ValidationError(Messages.NO_FAILED_PAYMENT_FOUND)

    return order, payment
