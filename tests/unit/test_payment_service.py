from decimal import Decimal
from types import SimpleNamespace

from backend.app.modules.payment import payment_service
from backend.app.modules.payment.gateway.stripe_gateway import StripeGateway


def test_calculate_order_total():
    order = SimpleNamespace(
        items=[
            SimpleNamespace(price=Decimal("10.00"), quantity=2),
            SimpleNamespace(price=5, quantity=1),
        ]
    )

    total = payment_service.calculate_order_total(order)
    assert total == Decimal("25.00")


def test_process_gateway_payment(monkeypatch):
    # Force mock mode: the test does not call the real Stripe API.
    monkeypatch.setattr(
        "backend.app.core.config.settings.STRIPE_SECRET_KEY",
        None,
    )

    from backend.app.modules.payment.gateway.base import PaymentRequest

    request = PaymentRequest(
        amount=Decimal("1.00"),
        method="card",
    )

    result = payment_service.process_gateway_payment(
        gateway=StripeGateway(),
        request=request,
        idempotency_key="abc123",
    )

    assert result.status == "approved"
    assert result.provider_payment_id.startswith("pi_test_")
