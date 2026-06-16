"""Tests for process_payment — the core payment processing use case.

Covers:
- Payment not found
- Invalid payment status (not PENDING or FAILED)
- PENDING payment → approved
- PENDING payment → failed
- FAILED payment → approved (retry scenario)
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.modules.payment import use_cases
from backend.app.modules.payment.gateway.base import (
    PaymentGatewayResult,
    PaymentRequest,
)


class FakeGateway:
    """Simulates a payment gateway with controllable results."""

    name = "fake"

    def __init__(self, result: PaymentGatewayResult | None = None) -> None:
        self._result = result
        self.captured_request: PaymentRequest | None = None
        self.captured_idempotency_key: str | None = None

    def process_payment(
        self,
        *,
        request: PaymentRequest,
        idempotency_key: str | None = None,
    ) -> PaymentGatewayResult:
        self.captured_request = request
        self.captured_idempotency_key = idempotency_key
        if self._result is not None:
            return self._result
        return PaymentGatewayResult(
            provider_payment_id="pi_fake",
            status="approved",
            failure_reason=None,
        )


def _make_payment(status: str = "pending", payment_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=payment_id,
        order_id=1,
        user_id=1,
        amount=Decimal("10.00"),
        status=status,
        provider="stripe",
        provider_payment_id=None,
        provider_status=None,
        provider_reference=None,
        failure_reason=None,
        created_at=None,
        updated_at=None,
    )


class TestProcessPaymentNotFound:
    """process_payment raises NotFoundError when payment_id does not exist."""

    def test_missing_payment_raises_not_found(self, monkeypatch) -> None:
        class PaymentRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, payment_id: int) -> None:
                return None

        monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

        uow = SimpleNamespace(session=object(), flush=lambda: None)
        with pytest.raises(NotFoundError, match="Payment not found"):
            use_cases.process_payment(
                payment_id=999,
                payment_method_id="pm_1",
                uow=uow,
                gateway=FakeGateway(),
            )


class TestProcessPaymentInvalidStatus:
    """process_payment rejects payments that are not PENDING or FAILED."""

    @pytest.mark.parametrize("status", ["approved", "cancelled", "refunded"])
    def test_rejects_non_processable_status(self, monkeypatch, status: str) -> None:
        class PaymentRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, payment_id: int) -> SimpleNamespace:
                return _make_payment(status=status)

        monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

        uow = SimpleNamespace(session=object(), flush=lambda: None)
        with pytest.raises(ValidationError, match="Invalid payment status"):
            use_cases.process_payment(
                payment_id=1,
                payment_method_id="pm_1",
                uow=uow,
                gateway=FakeGateway(),
            )


class TestProcessPaymentHappyPath:
    """Successful payment processing flows."""

    def test_pending_payment_approved_by_gateway(self, monkeypatch) -> None:
        class PaymentRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, payment_id: int) -> SimpleNamespace:
                return _make_payment(status="pending")

        monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

        gateway = FakeGateway()
        uow = SimpleNamespace(session=object(), flush=lambda: None)

        result = use_cases.process_payment(
            payment_id=1,
            payment_method_id="pm_success",
            uow=uow,
            gateway=gateway,
            idempotency_key="idem-1",
        )

        assert result.status == "approved"
        assert result.provider_payment_id == "pi_fake"
        assert result.failure_reason is None
        assert gateway.captured_idempotency_key == "idem-1"
        assert gateway.captured_request is not None
        assert gateway.captured_request.amount == Decimal("10.00")
        assert gateway.captured_request.provider_data == {
            "payment_method_id": "pm_success"
        }

    def test_pending_payment_declined_by_gateway(self, monkeypatch) -> None:
        class PaymentRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, payment_id: int) -> SimpleNamespace:
                return _make_payment(status="pending")

        monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

        gateway = FakeGateway(
            result=PaymentGatewayResult(
                provider_payment_id="pi_decline",
                status="failed",
                failure_reason="card_declined",
            )
        )
        uow = SimpleNamespace(session=object(), flush=lambda: None)

        result = use_cases.process_payment(
            payment_id=1, payment_method_id="pm_decline", uow=uow, gateway=gateway
        )

        assert result.status == "failed"
        assert result.failure_reason == "card_declined"
        assert result.provider_payment_id == "pi_decline"

    def test_failed_payment_retry_approved(self, monkeypatch) -> None:
        """A previously failed payment can be retried and succeed."""

        class PaymentRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, payment_id: int) -> SimpleNamespace:
                return _make_payment(status="failed")

        monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

        gateway = FakeGateway()
        uow = SimpleNamespace(session=object(), flush=lambda: None)

        result = use_cases.process_payment(
            payment_id=1, payment_method_id="pm_retry", uow=uow, gateway=gateway
        )

        assert result.status == "approved"
        assert result.provider_payment_id == "pi_fake"

    def test_gateway_result_applied_to_payment(self, monkeypatch) -> None:
        """All gateway result fields are applied to the payment object."""

        class PaymentRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, payment_id: int) -> SimpleNamespace:
                return _make_payment(status="pending")

        monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

        gateway = FakeGateway(
            result=PaymentGatewayResult(
                provider_payment_id="pi_full",
                status="approved",
                failure_reason=None,
                provider_status="succeeded",
                provider_reference="ref_001",
            )
        )
        uow = SimpleNamespace(session=object(), flush=lambda: None)

        result = use_cases.process_payment(
            payment_id=1, payment_method_id="pm_full", uow=uow, gateway=gateway
        )

        assert result.status == "approved"
        assert result.provider_payment_id == "pi_full"
        assert result.provider_status == "succeeded"
        assert result.provider_reference == "ref_001"
        assert result.failure_reason is None
