"""Payment use-cases: orchestrate payment flows and webhooks."""

from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.exceptions import Messages, NotFoundError, ValidationError
from backend.app.idempotency.helpers import (
    persist_idempotency_response,
    reserve_idempotency_key,
    try_replay,
)
from backend.app.idempotency.repositories import IdempotencyRepository
from backend.app.modules.order.domain.models import Order
from backend.app.modules.order.repositories.order_repository import OrderRepository
from backend.app.modules.payment.gateway.base import PaymentGateway
from backend.app.modules.payment.payment_service import (
    apply_gateway_result,
    assert_requester_can_access_order,
    calculate_order_total,
    create_payment_record,
    is_requester_allowed,
    process_gateway_payment,
)
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.modules.payment.schemas import (
    PaymentCreate,
    PaymentRead,
    PaymentWebhookPayload,
)


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
    """Orchestrate a payment processing flow."""

    _validate_idempotency_input(
        idempotency_key=idempotency_key,
        request_hash=request_hash,
    )

    payment_repository = PaymentRepository(uow.session)
    order_repository = OrderRepository(uow.session)
    idempotency_repository = IdempotencyRepository(uow.session)

    replay = _try_payment_replay_if_possible(
        repository=idempotency_repository,
        idempotency_key=idempotency_key,
        user_id=requesting_user_id,
    )

    if replay is not None:
        return replay

    try:
        order = _get_order_or_raise(
            repository=order_repository,
            order_id=payment_data.order_id,
        )

        assert_requester_can_access_order(
            order,
            requesting_user_id,
            uow,
        )

        amount = calculate_order_total(order)

        _reserve_payment_idempotency_if_needed(
            repository=idempotency_repository,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            user_id=requesting_user_id,
        )

        if idempotency_key is not None:
            uow.commit()

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

        payment_read = PaymentRead.model_validate(payment)

        _persist_payment_idempotent_response_if_needed(
            repository=idempotency_repository,
            payment_read=payment_read,
            idempotency_key=idempotency_key,
            user_id=requesting_user_id,
        )

        if commit:
            uow.commit()

        return payment_read

    except Exception:
        uow.rollback()
        if idempotency_key is not None and requesting_user_id is not None:
            idempotency_repository.delete_by_key(idempotency_key, requesting_user_id)
            uow.commit()
        raise


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
    payload: PaymentWebhookPayload,
    uow: UnitOfWork,
) -> PaymentRead:
    """Process a provider webhook payload."""
    repository = PaymentRepository(uow.session)

    payment = repository.get_by_provider_payment_id(payload.provider_payment_id)
    if payment is None:
        raise NotFoundError(Messages.PAYMENT_NOT_FOUND)

    # if provider name differs and we received one, update the record
    if provider_name and provider_name != getattr(payment, "provider", None):
        payment.provider = provider_name

    payment.status = payload.status
    payment.failure_reason = payload.failure_reason

    repository.update(payment)
    uow.commit()

    return PaymentRead.model_validate(payment)


def _validate_idempotency_input(
    idempotency_key: str | None,
    request_hash: str | None,
) -> None:
    if bool(idempotency_key) != bool(request_hash):
        raise ValidationError(
            "Both idempotency_key and request_hash must be provided together."
        )


def _try_payment_replay_if_possible(
    repository: IdempotencyRepository,
    idempotency_key: str | None,
    user_id: int | None,
) -> PaymentRead | None:
    if idempotency_key is None:
        return None

    raw = try_replay(
        repository=repository,
        key=idempotency_key,
        user_id=user_id,
    )

    if raw is None:
        return None

    return PaymentRead.model_validate(raw)


def _reserve_payment_idempotency_if_needed(
    repository: IdempotencyRepository,
    idempotency_key: str | None,
    request_hash: str | None,
    user_id: int | None,
) -> None:
    if idempotency_key is None or request_hash is None or user_id is None:
        return

    reserve_idempotency_key(
        repository=repository,
        key=idempotency_key,
        user_id=user_id,
        request_hash=request_hash,
    )


def _persist_payment_idempotent_response_if_needed(
    repository: IdempotencyRepository,
    payment_read: PaymentRead,
    idempotency_key: str | None,
    user_id: int | None,
) -> None:
    if idempotency_key is None or user_id is None:
        return

    persist_idempotency_response(
        repository=repository,
        key=idempotency_key,
        user_id=user_id,
        status=201,
        body=payment_read.model_dump_json(),
    )


def _get_order_or_raise(
    repository: OrderRepository,
    order_id: int,
) -> Order:
    order = repository.get_by_id(order_id)

    if order is None:
        raise NotFoundError(Messages.ORDER_NOT_FOUND)

    return order
