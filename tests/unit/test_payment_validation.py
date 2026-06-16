"""Payment validation tests adapted for current architecture.

process_payment no longer accepts requesting_user_id, request_hash or
PaymentCreate. calculate_order_total and assert_requester_can_access_order
no longer exist in the codebase.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.modules.payment import use_cases


def test_process_payment_rejects_invalid_status() -> None:
    """process_payment raises ValidationError when payment is not PENDING or FAILED."""

    class PaymentRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, payment_id: int) -> SimpleNamespace:
            return SimpleNamespace(
                id=payment_id,
                order_id=1,
                user_id=1,
                amount=Decimal("10.00"),
                status="approved",
                provider="stripe",
                failure_reason=None,
            )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

    class FakeGateway:
        name = "fake"

        def process_payment(self, *, request, idempotency_key=None):
            from backend.app.modules.payment.gateway.base import PaymentGatewayResult

            return PaymentGatewayResult(
                provider_payment_id="pi_fake",
                status="approved",
                failure_reason=None,
            )

    uow = SimpleNamespace(session=object(), flush=lambda: None)
    with pytest.raises(ValidationError, match="Invalid payment status"):
        use_cases.process_payment(
            payment_id=1,
            payment_method_id="pm_1",
            uow=uow,
            gateway=FakeGateway(),
        )

    monkeypatch.undo()


def test_process_payment_raises_not_found_when_missing() -> None:
    """process_payment raises NotFoundError when payment does not exist."""

    class PaymentRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, payment_id: int) -> None:
            return None

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

    class FakeGateway:
        name = "fake"

        def process_payment(self, *, request, idempotency_key=None):
            from backend.app.modules.payment.gateway.base import PaymentGatewayResult

            return PaymentGatewayResult(
                provider_payment_id="pi_fake",
                status="approved",
                failure_reason=None,
            )

    uow = SimpleNamespace(session=object(), flush=lambda: None)
    with pytest.raises(NotFoundError, match="Payment not found"):
        use_cases.process_payment(
            payment_id=999,
            payment_method_id="pm_1",
            uow=uow,
            gateway=FakeGateway(),
        )

    monkeypatch.undo()
