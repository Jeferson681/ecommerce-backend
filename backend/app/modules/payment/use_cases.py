"""Payment Use Cases"""

from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.exceptions import Messages, NotFoundError
from backend.app.idempotency.repositories import IdempotencyRepository
from backend.app.modules.order.repositories.order_repository import OrderRepository
from backend.app.modules.payment.gateway.base import PaymentGateway
from backend.app.modules.payment.payment_service import (
    apply_gateway_result,
    assert_requester_can_access_order,
    calculate_order_total,
    create_payment_record,
    get_order_or_raise,
    is_requester_allowed,
    persist_payment_idempotent_response,
    process_gateway_payment,
    reserve_payment_idempotency,
    try_replay_payment,
    validate_idempotency_input,
)
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.modules.payment.schemas import PaymentCreate, PaymentRead


def process_payment(
    payment_data: PaymentCreate,
    uow: UnitOfWork,
    *,
    requesting_user_id: int | None = None,
    idempotency_key: str | None = None,
    request_hash: str | None = None,
    gateway: PaymentGateway | None = None,
    commit: bool = True,
) -> PaymentRead:
    """Orchestrate a payment processing flow.

    Flow (explicit):
    - validate idempotency inputs
    - try replay via idempotency repository
    - load and validate order + access
    - reserve idempotency key
    - create a pending payment record
    - call payment gateway
    - apply gateway result and persist
    - persist idempotent response and commit
    """

    validate_idempotency_input(idempotency_key, request_hash)

    payment_repository = PaymentRepository(uow.session)
    order_repository = OrderRepository(uow.session)
    idempotency_repository = IdempotencyRepository(uow.session)

    replay = try_replay_payment(
        repository=idempotency_repository,
        idempotency_key=idempotency_key,
        user_id=requesting_user_id,
    )
    if replay is not None:
        return replay

    try:
        order = get_order_or_raise(order_repository, payment_data.order_id)
        assert_requester_can_access_order(order, requesting_user_id, uow)

        amount = calculate_order_total(order)

        reserve_payment_idempotency(
            repository=idempotency_repository,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            user_id=requesting_user_id,
        )

        provider_name = gateway.name if gateway is not None else "stripe"

        payment = create_payment_record(
            repository=payment_repository,
            order=order,
            amount=amount,
            provider_name=provider_name,
        )

        gateway_result = process_gateway_payment(
            gateway=gateway,
            order_id=order.id,
            user_id=order.user_id,
            amount=amount,
            idempotency_key=idempotency_key,
        )

        apply_gateway_result(payment, gateway_result)
        payment_repository.update(payment)
        uow.flush()

        persist_payment_idempotent_response(
            repository=idempotency_repository,
            payment_repository=payment_repository,
            payment_id=payment.id,
            idempotency_key=idempotency_key,
            user_id=requesting_user_id,
        )

        if commit:
            uow.commit()

    except Exception:
        uow.rollback()
        raise

    refreshed = payment_repository.get_by_id(payment.id)
    if refreshed is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    return PaymentRead.model_validate(refreshed)


def get_payment(
    payment_id: int,
    uow: UnitOfWork,
    *,
    requesting_user_id: int | None = None,
) -> PaymentRead:
    repository = PaymentRepository(uow.session)
    payment = repository.get_by_id(payment_id)

    if payment is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    if not is_requester_allowed(payment.order_id, requesting_user_id, uow):
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    return PaymentRead.model_validate(payment)


def list_payments(uow: UnitOfWork) -> list[PaymentRead]:
    repository = PaymentRepository(uow.session)
    payments = repository.list()

    return [PaymentRead.model_validate(payment) for payment in payments]


def process_provider_webhook(
    provider_name: str,
    payload: dict[str, object],
    uow: UnitOfWork,
) -> PaymentRead:
    """Process a provider webhook payload.

    Expected minimal payload keys (generic):
    - provider_payment_id: str
    - status: str (pending/approved/failed/cancelled/refunded)
    - failure_reason: optional str
    """
    repository = PaymentRepository(uow.session)

    provider_payment_id = payload.get("provider_payment_id")
    if not isinstance(provider_payment_id, str) or not provider_payment_id:
        raise ValueError("provider_payment_id missing or invalid in webhook payload")

    payment = repository.get_by_provider_payment_id(provider_payment_id)
    if payment is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    # if provider name differs and we received one, update the record
    if provider_name and provider_name != getattr(payment, "provider", None):
        payment.provider = provider_name

    # apply fields from payload
    status = payload.get("status")
    failure_reason = payload.get("failure_reason")

    # validate status against allowed values to avoid invalid updates
    allowed_statuses = {"pending", "approved", "failed", "cancelled", "refunded"}
    if isinstance(status, str):
        if status not in allowed_statuses:
            raise ValueError(f"invalid payment status in webhook payload: {status}")
        payment.status = status

    if failure_reason is None:
        pass
    elif isinstance(failure_reason, str):
        payment.failure_reason = failure_reason

    repository.update(payment)
    uow.commit()

    refreshed = repository.get_by_id(payment.id)
    if refreshed is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    return PaymentRead.model_validate(refreshed)
