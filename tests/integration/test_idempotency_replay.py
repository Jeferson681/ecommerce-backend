"""Tests for idempotency replay behavior.

Validates that replaying a successful checkout request with the same
idempotency key returns the same response and does NOT create duplicate
orders or payments.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.api.routers.order import get_current_user_id
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.product.domain.models import Product

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_checkout_then_replay_returns_same() -> None:
    session = SessionLocal()

    product = Product(
        name="P-replay", description="d", price=Decimal("3.00"), stock_quantity=5
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    # prepare cart for user 77
    from backend.app.modules.cart.domain.models import Cart, CartItem

    cart = Cart(user_id=77)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    session.add(item)
    session.commit()

    app.dependency_overrides[get_current_user_id] = lambda: 77

    key = "replay-key-1"

    resp1 = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
        headers={"Idempotency-Key": key},
    )
    assert resp1.status_code == 201
    body1 = resp1.json()

    resp2 = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
        headers={"Idempotency-Key": key},
    )
    assert resp2.status_code == 201
    body2 = resp2.json()

    # Same order must be returned (not a new one)
    assert body1["id"] == body2["id"]
    assert body1["user_id"] == body2["user_id"]
    assert body1["status"] == body2["status"]

    # Verify only ONE order exists in the database
    session2 = SessionLocal()
    from backend.app.modules.order.repositories.order_repository import (
        OrderRepository,
    )
    from backend.app.modules.payment.repositories.payment_repository import (
        PaymentRepository,
    )

    order_repo = OrderRepository(session2)
    orders = order_repo.get_by_user_id(77)
    assert len(orders) == 1, f"Expected 1 order, got {len(orders)}"

    # Verify only ONE payment exists for the order
    payment_repo = PaymentRepository(session2)
    payments = payment_repo.get_by_order_id(body1["id"])
    assert len(payments) == 1, f"Expected 1 payment, got {len(payments)}"

    session2.close()
    session.close()
