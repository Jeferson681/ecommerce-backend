from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError as PydanticValidationError

from backend.app.core.exceptions import NotFoundError
from backend.app.modules.payment import use_cases
from backend.app.modules.payment.schemas import (
    PaymentCreate,
    PaymentWebhookPayload,
)


class DummyUoW:
    def __init__(self) -> None:
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def flush(self) -> None:
        return None


def _make_order() -> SimpleNamespace:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return SimpleNamespace(
        id=1,
        user_id=1,
        items=[SimpleNamespace(price=Decimal("10.00"), quantity=1)],
        created_at=now,
        updated_at=now,
    )


def test_process_payment_happy_path(monkeypatch) -> None:
    uow = DummyUoW()

    class OrderRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, order_id: int):
            return _make_order()

    class PaymentRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def create(self, payment: object):
            payment.id = 1
            from datetime import UTC, datetime

            now = datetime.now(UTC)
            payment.created_at = now
            payment.updated_at = now
            return payment

        def update(self, payment: object):
            return payment

        def get_by_id(self, payment_id: int):
            from datetime import UTC, datetime

            now = datetime.now(UTC)

            return SimpleNamespace(
                id=payment_id,
                order_id=1,
                user_id=1,
                amount=Decimal("10.00"),
                status="approved",
                provider="stripe",
                provider_payment_id="pi_1",
                failure_reason=None,
                created_at=now,
                updated_at=now,
            )

    class IdempotencyRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_key(self, key: str, user_id: int | None = None):
            return None

        def claim(self, record: object):
            return (record, True)

        def save_response(self, key: str, user_id: int, status: int, body: str):
            pass

    class Gateway:
        name = "stripe"

        def process_payment(self, *, order_id, user_id, amount, idempotency_key=None):
            from backend.app.modules.payment.gateway.base import PaymentGatewayResult

            return PaymentGatewayResult(
                provider_payment_id="pi_1", status="approved", failure_reason=None
            )

    monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))
    monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))
    monkeypatch.setattr(
        use_cases, "IdempotencyRepository", lambda s: IdempotencyRepo(s)
    )

    payload = PaymentCreate(order_id=1)

    result = use_cases.process_payment(
        payload,
        uow,
        requesting_user_id=1,
        idempotency_key="k",
        request_hash="h",
        gateway=Gateway(),
    )

    assert result.id == 1
    assert uow.committed is True


def test_process_provider_webhook_happy_and_errors(monkeypatch) -> None:
    uow = DummyUoW()

    class PaymentRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_provider_payment_id(self, provider_payment_id: str):
            from datetime import UTC, datetime

            now = datetime.now(UTC)

            if provider_payment_id == "exists":
                return SimpleNamespace(
                    id=1,
                    order_id=1,
                    user_id=1,
                    amount=Decimal("10.00"),
                    status="pending",
                    provider="stripe",
                    provider_payment_id=provider_payment_id,
                    failure_reason=None,
                    created_at=now,
                    updated_at=now,
                )
            return None

        def update(self, payment: object):
            return payment

        def get_by_id(self, payment_id: int):
            from datetime import UTC, datetime

            now = datetime.now(UTC)

            return SimpleNamespace(
                id=payment_id,
                order_id=1,
                user_id=1,
                amount=Decimal("10.00"),
                status="approved",
                provider="stripe",
                provider_payment_id="exists",
                failure_reason=None,
                created_at=now,
                updated_at=now,
            )

    monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

    # happy path
    payload = PaymentWebhookPayload(
        provider_payment_id="exists",
        status="approved",
    )
    result = use_cases.process_provider_webhook("stripe", payload, uow)
    assert result.status == "approved"

    # invalid payload is rejected by the schema at the boundary
    with pytest.raises(PydanticValidationError):
        PaymentWebhookPayload(status="approved")

    # missing payment
    with pytest.raises(NotFoundError):
        use_cases.process_provider_webhook(
            "stripe",
            PaymentWebhookPayload(
                provider_payment_id="nope",
                status="approved",
            ),
            uow,
        )
