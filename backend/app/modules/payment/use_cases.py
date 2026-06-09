"""Use cases related to payments."""

from decimal import Decimal

from backend.app.core.exceptions import Messages, NotFoundError
from backend.app.modules.payment.domain.models import Payment
from backend.app.modules.payment.gateway.base import (
    PaymentGateway,
)
from backend.app.modules.payment.payment_service import (
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
        status="pending",
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
    Process an existing pending payment but don't commit to the database.
    """

    payment_repository = PaymentRepository(uow.session)

    payment = payment_repository.get_by_id(payment_id)

    if payment is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    if payment.status != "pending":
        raise ValueError("Only pending payments can be processed")

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
