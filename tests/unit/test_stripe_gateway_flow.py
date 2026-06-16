"""Tests for StripeGateway covering the payment_method_id flow via PaymentRequest."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import stripe

from backend.app.modules.payment.gateway.base import (
    PaymentRequest,
)
from backend.app.modules.payment.gateway.stripe_gateway import StripeGateway


def _make_request(
    amount: Decimal | None = None,
    method: str = "card",
    payment_method_id: str | None = "pm_test_123456",
) -> PaymentRequest:
    return PaymentRequest(
        amount=amount or Decimal("50.00"),
        method=method,  # type: ignore[arg-type]
        provider_data=(
            {"payment_method_id": payment_method_id} if payment_method_id else None
        ),
    )


class TestPaymentMethodIdValidation:
    """Gateway validates payment_method_id before calling Stripe API."""

    def test_missing_payment_method_id_returns_failed(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        gateway = StripeGateway()
        request = _make_request(payment_method_id=None)

        result = gateway.process_payment(request=request)

        assert result.status == "failed"
        assert result.failure_reason == "payment_method_id is required"
        assert result.provider_payment_id is None

    def test_missing_provider_data_returns_failed(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        gateway = StripeGateway()
        request = PaymentRequest(amount=Decimal("10.00"), method="card")

        result = gateway.process_payment(request=request)

        assert result.status == "failed"
        assert result.failure_reason == "payment_method_id is required"
        assert result.provider_payment_id is None

    def test_empty_provider_data_returns_failed(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        gateway = StripeGateway()
        request = PaymentRequest(
            amount=Decimal("10.00"),
            method="card",
            provider_data={},
        )

        result = gateway.process_payment(request=request)

        assert result.status == "failed"
        assert result.failure_reason == "payment_method_id is required"


class TestCreatePaymentIntent:
    """Exercises _create_payment_intent with a mocked Stripe API."""

    def _setup(self, monkeypatch) -> StripeGateway:
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        return StripeGateway()

    def _mock_intent(self, status="succeeded", last_error=None):
        mock_intent = MagicMock()
        mock_intent.id = "pi_3XYZ"
        mock_intent.status = status
        mock_intent.last_payment_error = last_error
        return mock_intent

    def test_successful_payment_intent(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        mock_intent = self._mock_intent("succeeded")
        monkeypatch.setattr("stripe.PaymentIntent.create", lambda **kwargs: mock_intent)

        gateway = StripeGateway()
        request = _make_request(amount=Decimal("30.00"))
        result = gateway.process_payment(request=request)

        assert result.provider_payment_id == "pi_3XYZ"
        assert result.status == "approved"
        assert result.provider_status == "succeeded"
        assert result.failure_reason is None

    def test_pending_payment_intent(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        mock_intent = self._mock_intent("processing")
        monkeypatch.setattr("stripe.PaymentIntent.create", lambda **kwargs: mock_intent)

        gateway = StripeGateway()
        request = _make_request()
        result = gateway.process_payment(request=request)

        assert result.status == "pending"
        assert result.provider_status == "processing"

    def test_card_error_returns_failed_with_user_message(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )

        class FakeCardError(stripe.CardError):
            def __init__(self):
                super().__init__(
                    "Your card was declined.",
                    param=None,
                    code="card_declined",
                )

        def _raise(*args, **kwargs):
            raise FakeCardError()

        monkeypatch.setattr("stripe.PaymentIntent.create", _raise)

        gateway = StripeGateway()
        request = _make_request()
        result = gateway.process_payment(request=request)

        assert result.status == "failed"
        assert result.failure_reason == "Your card was declined."
        assert result.provider_payment_id is None

    def test_stripe_error_returns_failed(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )

        class FakeStripeError(stripe.StripeError):
            pass

        def _raise(*args, **kwargs):
            raise FakeStripeError("rate limit exceeded", None)

        monkeypatch.setattr("stripe.PaymentIntent.create", _raise)

        gateway = StripeGateway()
        request = _make_request()
        result = gateway.process_payment(request=request)

        assert result.status == "failed"
        assert result.failure_reason == "rate limit exceeded"
        assert result.provider_payment_id is None

    def test_last_payment_error_extracted(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        mock_error = MagicMock()
        mock_error.message = "Insufficient funds."
        mock_intent = self._mock_intent("requires_payment_method", mock_error)
        monkeypatch.setattr("stripe.PaymentIntent.create", lambda **kwargs: mock_intent)

        gateway = StripeGateway()
        request = _make_request()
        result = gateway.process_payment(request=request)

        assert result.status == "failed"
        assert result.provider_status == "requires_payment_method"
        assert result.failure_reason == "Insufficient funds."

    def test_requires_action_mapped_to_pending(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        mock_intent = self._mock_intent("requires_action")
        monkeypatch.setattr("stripe.PaymentIntent.create", lambda **kwargs: mock_intent)

        gateway = StripeGateway()
        request = _make_request()
        result = gateway.process_payment(request=request)

        assert result.status == "pending"
        assert result.provider_status == "requires_action"

    def test_requires_capture_mapped_to_pending(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        mock_intent = self._mock_intent("requires_capture")
        monkeypatch.setattr("stripe.PaymentIntent.create", lambda **kwargs: mock_intent)

        gateway = StripeGateway()
        request = _make_request()
        result = gateway.process_payment(request=request)

        assert result.status == "pending"
        assert result.provider_status == "requires_capture"


class TestMapStatus:
    def test_succeeded(self):
        assert StripeGateway()._map_status("succeeded") == "approved"

    def test_processing(self):
        assert StripeGateway()._map_status("processing") == "pending"

    def test_requires_action(self):
        assert StripeGateway()._map_status("requires_action") == "pending"

    def test_requires_capture(self):
        assert StripeGateway()._map_status("requires_capture") == "pending"

    def test_requires_confirmation(self):
        assert StripeGateway()._map_status("requires_confirmation") == "pending"

    def test_requires_payment_method(self):
        assert StripeGateway()._map_status("requires_payment_method") == "failed"

    def test_canceled(self):
        assert StripeGateway()._map_status("canceled") == "cancelled"

    def test_unknown_status_falls_back_to_failed(self):
        assert StripeGateway()._map_status("unknown_garbage") == "failed"


class TestExtractFailureReason:
    def test_no_error_returns_none(self):
        intent = MagicMock(spec=[])
        assert StripeGateway._extract_failure_reason(intent) is None

    def test_error_with_message(self):
        intent = MagicMock()
        intent.last_payment_error = MagicMock()
        intent.last_payment_error.message = "Card declined."
        assert StripeGateway._extract_failure_reason(intent) == "Card declined."

    def test_error_without_message(self):
        intent = MagicMock()
        intent.last_payment_error = MagicMock()
        del intent.last_payment_error.message
        assert StripeGateway._extract_failure_reason(intent) is None


class TestIdempotencyKey:
    def test_idempotency_key_passed_to_stripe(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        captured_kwargs = {}

        def mock_create(**kwargs):
            captured_kwargs.update(kwargs)
            mock = MagicMock()
            mock.id = "pi_8MNO"
            mock.status = "succeeded"
            mock.last_payment_error = None
            return mock

        monkeypatch.setattr("stripe.PaymentIntent.create", mock_create)

        gateway = StripeGateway()
        request = _make_request()
        gateway.process_payment(request=request, idempotency_key="my-unique-key-123")
        assert captured_kwargs.get("idempotency_key") == "my-unique-key-123"

    def test_idempotency_key_none_when_omitted(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        captured_kwargs = {}

        def mock_create(**kwargs):
            captured_kwargs.update(kwargs)
            mock = MagicMock()
            mock.id = "pi_9PQR"
            mock.status = "succeeded"
            mock.last_payment_error = None
            return mock

        monkeypatch.setattr("stripe.PaymentIntent.create", mock_create)
        gateway = StripeGateway()
        request = _make_request()
        gateway.process_payment(request=request)
        assert captured_kwargs.get("idempotency_key") is None


class TestPaymentRequestContract:
    def test_gateway_accepts_payment_request(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_xxx"
        )
        mock_intent = MagicMock()
        mock_intent.id = "pi_contract"
        mock_intent.status = "succeeded"
        mock_intent.last_payment_error = None
        monkeypatch.setattr("stripe.PaymentIntent.create", lambda **kwargs: mock_intent)

        gateway = StripeGateway()
        request = PaymentRequest(
            amount=Decimal("99.99"),
            method="card",
            provider_data={"payment_method_id": "pm_contract_test"},
        )
        result = gateway.process_payment(request=request)
        assert result.status == "approved"
        assert result.provider_payment_id == "pi_contract"

    def test_gateway_refuses_old_signature(self):
        gateway = StripeGateway()
        with pytest.raises(TypeError):
            gateway.process_payment(
                order_id=1,
                user_id=1,
                amount=Decimal("10.00"),
                payment_method_id="pm_old",
            )

    def test_gateway_rejects_domain_entities(self):
        request = PaymentRequest(amount=Decimal("10.00"), method="card")
        assert not hasattr(request, "order_id")
        assert not hasattr(request, "user_id")
        assert not hasattr(request, "payment_method_id")


class TestMissingSecretKey:
    """Gateway raises ValueError when STRIPE_SECRET_KEY is not set."""

    def test_raises_on_missing_key(self, monkeypatch):
        monkeypatch.setattr("backend.app.core.config.settings.STRIPE_SECRET_KEY", None)
        gateway = StripeGateway()
        request = _make_request()
        with pytest.raises(ValueError, match="Stripe secret key is not configured"):
            gateway.process_payment(request=request)
