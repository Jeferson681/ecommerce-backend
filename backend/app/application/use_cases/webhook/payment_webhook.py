"""Payment webhook use case.

Responsibility: synchronize payment state from provider events.
"""

from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.modules.order.domain.models import OrderStatus
from backend.app.modules.order.repositories.order_repository import OrderRepository
from backend.app.modules.order.services import get_order_or_raise
from backend.app.modules.payment.domain.models import PaymentStatus
from backend.app.modules.payment.gateway.base import PaymentGateway
from backend.app.modules.payment.helpers import process_gateway_webhook
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.uow.unit_of_work import UnitOfWork


def process_provider_webhook(
    payload_bytes: bytes,
    signature: str | None,
    uow: UnitOfWork,
    *,
    gateway: PaymentGateway,
) -> None:
    """
    Synchronize payment state from a provider webhook.
    """

    payload = process_gateway_webhook(
        gateway=gateway,
        payload_bytes=payload_bytes,
        signature=signature,
    )

    if payload.provider_payment_id is None:
        raise ValidationError("Webhook payload missing provider_payment_id")

    payment_repository = PaymentRepository(uow.session)
    order_repository = OrderRepository(uow.session)

    payment = payment_repository.get_by_provider_payment_id(
        payload.provider_payment_id,
    )

    if payment is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    order = get_order_or_raise(order_repository, payment.order_id)

    payment.status = payload.status
    payment.provider_status = payload.provider_status
    payment.failure_reason = payload.failure_reason

    if payment.status == PaymentStatus.APPROVED:
        order.status = OrderStatus.PAID

    uow.commit()
