"""Payment webhook use case.

Responsibility: synchronize payment state from provider events.
"""

from backend.app.core.exceptions import Messages, NotFoundError
from backend.app.modules.order.repositories.order_repository import OrderRepository
from backend.app.modules.payment.gateway.base import (
    PaymentGateway,
)
from backend.app.modules.payment.payment_service import (
    ORDER_STATUS_PAID,
    PAYMENT_STATUS_APPROVED,
    process_gateway_webhook,
)
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.uow.unit_of_work import UnitOfWork


def process_provider_webhook(
    payload_bytes: bytes,
    stripe_signature: str | None,
    uow: UnitOfWork,
    *,
    gateway: PaymentGateway,
    idempotency_key: str | None = None,
) -> None:
    """
    Synchronize payment state from Stripe webhook.
    """

    payload = process_gateway_webhook(
        gateway=gateway,
        payload_bytes=payload_bytes,
        signature=stripe_signature,
        idempotency_key=idempotency_key,
    )

    if payload.provider_payment_id is None:
        raise ValueError("Webhook payload missing provider_payment_id")

    payment_repository = PaymentRepository(uow.session)
    order_repository = OrderRepository(uow.session)

    payment = payment_repository.get_by_provider_payment_id(
        payload.provider_payment_id,
    )

    if payment is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    order = order_repository.get_by_id(payment.order_id)

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    payment.status = payload.status
    payment.provider_status = payload.provider_status
    payment.failure_reason = payload.failure_reason

    if payment.status == PAYMENT_STATUS_APPROVED:
        order.status = ORDER_STATUS_PAID

    uow.commit()
