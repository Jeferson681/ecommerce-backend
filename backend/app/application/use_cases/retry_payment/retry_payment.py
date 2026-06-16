"""Retry Payment Use Case.
responsible for retrying a payment that has failed."""

import logging

from backend.app.application.use_cases.retry_payment.services import (
    get_pending_order_and_failed_payment,
)
from backend.app.idempotency.helpers import (
    reserve_idempotency_if_needed,
    validate_idempotency_input,
)
from backend.app.idempotency.repositories import IdempotencyRepository
from backend.app.modules.order.domain.models import OrderStatus
from backend.app.modules.order.repositories.order_repository import (
    OrderRepository,
)
from backend.app.modules.order.schemas import OrderRead
from backend.app.modules.order.use_cases import (
    persist_idempotent_response_if_needed,
    try_order_response_replay,
)
from backend.app.modules.payment.domain.models import PaymentStatus
from backend.app.modules.payment.gateway.base import PaymentGateway
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.modules.payment.use_cases import (
    process_payment,
)
from backend.app.uow.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


def retry_payment(
    user_id: int,
    order_id: int,
    uow: UnitOfWork,
    *,
    payment_method_id: str,
    gateway: PaymentGateway,
    idempotency_key: str | None = None,
    request_hash: str | None = None,
) -> OrderRead:
    """Retry a payment for the authenticated user."""

    validate_idempotency_input(idempotency_key, request_hash)

    order_repository = OrderRepository(uow.session)
    payment_repository = PaymentRepository(uow.session)
    idempotency_repository = IdempotencyRepository(uow.session)

    replay = try_order_response_replay(
        repository=idempotency_repository,
        idempotency_key=idempotency_key,
        user_id=user_id,
    )

    if replay is not None:
        return replay

    reserve_idempotency_if_needed(
        repository=idempotency_repository,
        idempotency_key=idempotency_key,
        user_id=user_id,
        request_hash=request_hash,
    )

    if idempotency_key is not None:
        uow.commit()

    try:
        order, payment = get_pending_order_and_failed_payment(
            order_repository=order_repository,
            payment_repository=payment_repository,
            order_id=order_id,
            user_id=user_id,
        )

        payment = process_payment(
            payment_id=payment.id,
            payment_method_id=payment_method_id,
            uow=uow,
            gateway=gateway,
            idempotency_key=idempotency_key,
        )

        if payment.status == PaymentStatus.APPROVED:
            order.status = OrderStatus.PAID

        uow.flush()

        persist_idempotent_response_if_needed(
            repository=idempotency_repository,
            order_repository=order_repository,
            order_id=order.id,
            idempotency_key=idempotency_key,
            user_id=user_id,
        )

        uow.commit()

        return OrderRead.model_validate(order)

    except Exception:
        # If an exception occurs after the idempotency key was claimed
        # and committed, the session is in an invalid state.
        # First rollback the session, then delete the stuck key.
        if idempotency_key is not None:
            try:
                uow.rollback()
                idempotency_repository.delete_by_key(
                    idempotency_key,
                    user_id,
                )
                uow.commit()
            except Exception as cleanup_err:
                logger.exception(
                    "Failed to release idempotency key %s: %s",
                    idempotency_key,
                    cleanup_err,
                )
        raise
