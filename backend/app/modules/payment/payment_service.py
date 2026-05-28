"""Payment helpers for payment flows."""

from __future__ import annotations

from decimal import Decimal

from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.exceptions import Messages, NotFoundError
from backend.app.modules.order.domain.models import Order
from backend.app.modules.order.repositories.order_repository import OrderRepository
from backend.app.modules.payment.domain.models import Payment
from backend.app.modules.payment.gateway.base import (
    PaymentGateway,
    PaymentGatewayResult,
)
from backend.app.modules.payment.gateway.stripe_gateway import StripeGateway
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.modules.user.repositories.user_repository import UserRepository

PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_APPROVED = "approved"
PAYMENT_STATUS_FAILED = "failed"
PAYMENT_STATUS_CANCELLED = "cancelled"
PAYMENT_STATUS_REFUNDED = "refunded"


def assert_requester_can_access_order(
    order: Order,
    requesting_user_id: int | None,
    uow: UnitOfWork,
) -> None:
    if requesting_user_id is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    if order.user_id == requesting_user_id:
        return

    user_repository = UserRepository(uow.session)
    requester = user_repository.get_by_id(requesting_user_id)

    if requester is not None and requester.role == "admin":
        return

    raise NotFoundError(Messages.ORDER_NOT_FOUND)


def is_requester_allowed(
    order_id: int,
    requesting_user_id: int | None,
    uow: UnitOfWork,
) -> bool:
    if requesting_user_id is None:
        return False

    order_repository = OrderRepository(uow.session)
    order = order_repository.get_by_id(order_id)

    if order is None:
        return False

    if order.user_id == requesting_user_id:
        return True

    user_repository = UserRepository(uow.session)
    requester = user_repository.get_by_id(requesting_user_id)

    return requester is not None and requester.role == "admin"


def calculate_order_total(order: Order) -> Decimal:
    """Compute the total amount for an order (Decimal).

    Uses the authoritative product price stored on the order items.
    """
    total = Decimal("0")

    for item in order.items:
        total += Decimal(str(item.price)) * Decimal(str(item.quantity))

    return total


def create_payment_record(
    repository: PaymentRepository,
    order: Order,
    amount: Decimal,
    provider_name: str,
) -> Payment:
    """Create and persist a pending Payment record.

    Repository remains responsible only for persistence; no commit here.
    """
    payment = Payment(
        order_id=order.id,
        user_id=order.user_id,
        amount=amount,
        status=PAYMENT_STATUS_PENDING,
        provider=provider_name,
    )

    return repository.create(payment)


def apply_gateway_result(
    payment: Payment,
    gateway_result: PaymentGatewayResult,
) -> None:
    payment.provider_payment_id = gateway_result.provider_payment_id
    payment.status = gateway_result.status
    payment.failure_reason = gateway_result.failure_reason


def process_gateway_payment(
    gateway: PaymentGateway | None,
    order_id: int,
    user_id: int,
    amount: Decimal,
    idempotency_key: str | None,
) -> PaymentGatewayResult:
    """Call the selected gateway (or Stripe test gateway) and return result.

    Keep gateway layer minimal — default to test `StripeGateway`.
    """
    selected_gateway = gateway or StripeGateway()

    return selected_gateway.process_payment(
        order_id=order_id,
        user_id=user_id,
        amount=amount,
        idempotency_key=idempotency_key,
    )
