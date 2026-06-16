"""process_gateway_payment now raises ValueError when STRIPE_SECRET_KEY is not configured.

The StripeGateway no longer has a mock mode fallback — it requires a configured
STRIPE_SECRET_KEY to operate. process_gateway_payment passes calls through to
the gateway directly.
"""

from decimal import Decimal

from backend.app.modules.payment.gateway.base import (
    PaymentGatewayResult,
    PaymentRequest,
)
from backend.app.modules.payment.payment_service import (
    build_payment_request,
    process_gateway_payment,
)


def test_build_payment_request() -> None:
    """build_payment_request creates a PaymentRequest with correct fields."""
    request = build_payment_request(
        amount=Decimal("25.00"),
        payment_method_id="pm_test_123",
    )
    assert request.amount == Decimal("25.00")
    assert request.method == "card"
    assert request.provider_data == {"payment_method_id": "pm_test_123"}


def test_process_gateway_payment_delegates_to_gateway() -> None:
    """process_gateway_payment returns the gateway's result unchanged."""

    class FakeGateway:
        name = "fake"

        def process_payment(
            self, *, request: PaymentRequest, idempotency_key: str | None = None
        ) -> PaymentGatewayResult:
            return PaymentGatewayResult(
                provider_payment_id="pi_fake",
                status="approved",
                failure_reason=None,
            )

    request = PaymentRequest(amount=Decimal("10.00"), method="card")
    result = process_gateway_payment(
        gateway=FakeGateway(),
        request=request,
        idempotency_key="abc123",
    )

    assert result.status == "approved"
    assert result.provider_payment_id == "pi_fake"


def test_process_gateway_payment_passes_idempotency_key() -> None:
    """The idempotency_key is forwarded to the gateway."""

    class CheckKeyGateway:
        name = "check"

        def process_payment(
            self, *, request: PaymentRequest, idempotency_key: str | None = None
        ) -> PaymentGatewayResult:
            assert idempotency_key == "my-key"
            return PaymentGatewayResult(
                provider_payment_id="pi_check", status="approved"
            )

    request = PaymentRequest(amount=Decimal("5.00"), method="card")
    result = process_gateway_payment(
        gateway=CheckKeyGateway(),
        request=request,
        idempotency_key="my-key",
    )
    assert result.provider_payment_id == "pi_check"
