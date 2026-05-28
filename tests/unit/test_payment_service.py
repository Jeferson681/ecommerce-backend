from decimal import Decimal
from types import SimpleNamespace

from backend.app.modules.payment import payment_service


def test_calculate_order_total():
    order = SimpleNamespace(
        items=[
            SimpleNamespace(price=Decimal("10.00"), quantity=2),
            SimpleNamespace(price=5, quantity=1),
        ]
    )

    total = payment_service.calculate_order_total(order)
    assert total == Decimal("25.00")


def test_process_gateway_payment_default():
    result = payment_service.process_gateway_payment(
        gateway=None,
        order_id=1,
        user_id=2,
        amount=Decimal("1.00"),
        idempotency_key="abc123",
    )

    assert result.status == "approved"
    assert result.provider_payment_id.startswith("pi_test_")
