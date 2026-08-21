"""Unit tests for retry_payment use case."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.app.application.use_cases.retry_payment import retry_payment
from backend.app.modules.payment.domain.models import PaymentStatus
from backend.app.modules.payment.gateway.base import PaymentGatewayResult
from backend.app.uow.unit_of_work import UnitOfWork


class DummyUoW(UnitOfWork):
    def __init__(self) -> None:
        super().__init__(lambda: Mock())
        self.committed = False
        self.rolled_back = False
        self.attach(Mock())

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def flush(self) -> None:
        pass


class NullIdempotencyRepo:
    """Idempotency repo that always returns None from replay/reserve flows."""

    def get_by_key(self, *args, **kwargs):
        return None

    def try_replay(self, *args, **kwargs):
        return None

    def reserve(self, *args, **kwargs):
        return None

    def claim(self, *args, **kwargs):
        return SimpleNamespace(id=1, key="", user_id=1, request_hash=""), True

    def save_response(self, *args, **kwargs):
        return None

    def delete_by_key(self, *args, **kwargs):
        return None


def _patch_services(
    monkeypatch,
    *,
    replay=None,
    order_status="pending",
    gateway_result=None,
    gateway_error=None,
):
    """Patch service functions in the retry_payment module namespace."""
    import importlib

    rp = importlib.import_module(
        "backend.app.application.use_cases.retry_payment.retry_payment"
    )

    # Patch repository class so delete_by_key works during cleanup.
    monkeypatch.setattr(
        rp, "IdempotencyRepository", lambda session: NullIdempotencyRepo()
    )
    monkeypatch.setattr(rp, "validate_idempotency_input", lambda *a, **kw: None)
    monkeypatch.setattr(rp, "try_order_response_replay", lambda *a, **kw: replay)
    monkeypatch.setattr(rp, "reserve_idempotency_if_needed", lambda *a, **kw: None)

    monkeypatch.setattr(
        rp,
        "get_pending_order_for_user",
        lambda *a, **kw: SimpleNamespace(id=1, user_id=1, status=order_status),
    )
    monkeypatch.setattr(
        rp,
        "get_failed_payment_for_order",
        lambda *a, **kw: SimpleNamespace(
            id=1,
            order_id=1,
            user_id=1,
            amount=Decimal("10.00"),
            status=PaymentStatus.FAILED,
            provider="stripe",
        ),
    )

    if gateway_error is not None:

        def _process_payment(*a, **kw):
            raise gateway_error
    else:

        def _process_payment(*a, **kw):
            payment = SimpleNamespace(
                id=1,
                order_id=1,
                user_id=1,
                amount=Decimal("10.00"),
                status=PaymentStatus.FAILED,
                provider="stripe",
            )
            payment.status = gateway_result.status
            return payment

    monkeypatch.setattr(rp, "process_payment", _process_payment)
    monkeypatch.setattr(
        rp, "persist_idempotent_response_if_needed", lambda *a, **kw: None
    )

    # OrderRead.model_validate is called on the SimpleNamespace order.
    # Patch the schema to a passthrough so Pydantic validation is skipped.
    class _FakeOrderRead:
        @staticmethod
        def model_validate(obj):
            return obj

    monkeypatch.setattr(rp, "OrderRead", _FakeOrderRead)

    return rp


def test_retry_payment_happy_path(monkeypatch) -> None:
    """Test successful payment retry."""
    uow = DummyUoW()

    _patch_services(
        monkeypatch,
        gateway_result=PaymentGatewayResult(
            provider_payment_id="pi_retry_1",
            status=PaymentStatus.APPROVED,
            failure_reason=None,
        ),
    )

    result = retry_payment(
        user_id=1,
        order_id=1,
        uow=uow,
        payment_method_id="pm_retry_123",
        gateway=Mock(),  # type: ignore
        idempotency_key="retry-key-123",
        request_hash="hash-123",
    )

    assert result.id == 1
    assert result.status == "paid"
    assert uow.committed is True


def test_retry_payment_idempotency_replay(monkeypatch) -> None:
    """Test that idempotency replay returns cached result."""
    uow = DummyUoW()

    cached_order = SimpleNamespace(id=1, user_id=1, status="paid")
    _patch_services(monkeypatch, replay=cached_order)

    result = retry_payment(
        user_id=1,
        order_id=1,
        uow=uow,
        payment_method_id="pm_123",
        gateway=Mock(),  # type: ignore
        idempotency_key="replay-key-123",
        request_hash="hash-123",
    )

    assert result == cached_order
    assert uow.committed is False


def test_retry_payment_gateway_failure(monkeypatch) -> None:
    """Test retry when payment gateway returns failure."""
    uow = DummyUoW()

    _patch_services(
        monkeypatch,
        order_status="pending",
        gateway_result=PaymentGatewayResult(
            provider_payment_id=None,
            status=PaymentStatus.FAILED,
            failure_reason="insufficient funds",
        ),
    )

    result = retry_payment(
        user_id=1,
        order_id=1,
        uow=uow,
        payment_method_id="pm_123",
        gateway=Mock(),  # type: ignore
        idempotency_key="key-123",
        request_hash="hash-123",
    )

    assert result.id == 1
    assert result.status == "pending"  # Not updated on failure
    assert uow.committed is True


def test_retry_payment_cleanup_on_exception(monkeypatch) -> None:
    """Test that idempotency key is cleaned up on exception."""
    uow = DummyUoW()

    _patch_services(
        monkeypatch,
        order_status="pending",
        gateway_error=RuntimeError("Gateway error"),
    )

    with pytest.raises(RuntimeError, match="Gateway error"):
        retry_payment(
            user_id=1,
            order_id=1,
            uow=uow,
            payment_method_id="pm_123",
            gateway=Mock(),  # type: ignore
            idempotency_key="cleanup-key-123",
            request_hash="hash-123",
        )

    assert uow.rolled_back is True


def test_retry_payment_cleanup_failure_logs_exception(monkeypatch) -> None:
    """Test that cleanup failure is logged but original exception is re-raised."""
    uow = DummyUoW()

    # Patch services with a gateway that fails.
    _patch_services(
        monkeypatch,
        order_status="pending",
        gateway_error=RuntimeError("Gateway error"),
    )

    # Patch IdempotencyRepository to raise ValueError on delete_by_key.
    class FailingIdempotencyRepo(NullIdempotencyRepo):
        def delete_by_key(self, *args, **kwargs):
            raise ValueError("DB error during cleanup")

    import importlib

    rp = importlib.import_module(
        "backend.app.application.use_cases.retry_payment.retry_payment"
    )
    monkeypatch.setattr(
        rp, "IdempotencyRepository", lambda session: FailingIdempotencyRepo()
    )

    with pytest.raises(RuntimeError, match="Gateway error"):
        retry_payment(
            user_id=1,
            order_id=1,
            uow=uow,
            payment_method_id="pm_123",
            gateway=Mock(),  # type: ignore
            idempotency_key="cleanup-key-123",
            request_hash="hash-123",
        )

    assert uow.rolled_back is True
