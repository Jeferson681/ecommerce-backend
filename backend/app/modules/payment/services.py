"""Services related to payments."""

from decimal import Decimal

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.payment.domain.models import Payment, PaymentStatus
from backend.app.modules.payment.gateway.base import (
    PaymentGateway,
)
from backend.app.modules.payment.helpers import (
    apply_gateway_result,
    build_payment_request,
    process_gateway_payment,
)
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.uow.unit_of_work import UnitOfWork


def create_payment(
    order_id: int,
    user_id: int,
    amount: Decimal,
    uow: UnitOfWork,
    provider: str = "stripe",
) -> Payment:
    """
    Create a payment intent.

    Creates a Payment in PENDING state.
    Does not communicate with gateways.
    Does not update Order status.
    """

    repository = PaymentRepository(uow.session)

    payment = Payment(
        order_id=order_id,
        user_id=user_id,
        amount=amount,
        status=PaymentStatus.PENDING,
        provider=provider,
    )

    repository.create(payment)

    uow.flush()

    return payment


def process_payment(
    payment_id: int,
    payment_method_id: str,
    uow: UnitOfWork,
    *,
    gateway: PaymentGateway,
    idempotency_key: str | None = None,
) -> Payment:
    """
    Process an existing pending or failed payment but don't commit to the database.
    """

    payment_repository = PaymentRepository(uow.session)

    payment = payment_repository.get_by_id(payment_id)

    if payment is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    if payment.status not in (PaymentStatus.PENDING, PaymentStatus.FAILED):
        raise ValidationError(Messages.INVALID_PAYMENT_STATUS)

    request = build_payment_request(
        amount=payment.amount,
        payment_method_id=payment_method_id,
    )

    result = process_gateway_payment(
        gateway=gateway,
        request=request,
        idempotency_key=idempotency_key,
    )

    apply_gateway_result(
        payment,
        result,
    )

    return payment


def get_failed_payment_for_order(
    payment_repository: PaymentRepository,
    *,
    order_id: int,
) -> Payment:
    payments = payment_repository.get_by_order_id(order_id)

    for payment in payments:
        if payment.status == PaymentStatus.FAILED:
            return payment

    raise ValidationError(Messages.NO_FAILED_PAYMENT_FOUND)
