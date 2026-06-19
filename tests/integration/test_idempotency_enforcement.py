"""Integration tests for mandatory idempotency enforcement on checkout and retry-payment."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.api.routers.order import get_current_user_id
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.cart.domain.models import Cart, CartItem
from backend.app.modules.order.repositories.order_repository import OrderRepository
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.modules.product.domain.models import Product

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def _setup_cart_and_product(user_id: int) -> None:
    session = SessionLocal()
    product = Product(
        name="Test Product", description="d", price=Decimal("9.99"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    cart = Cart(user_id=user_id)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    session.add(item)
    session.commit()
    session.close()


def test_checkout_missing_idempotency_key_returns_400() -> None:
    """Checkout without Idempotency-Key header must return 400/422."""
    _setup_cart_and_product(100)

    app.dependency_overrides[get_current_user_id] = lambda: 100

    resp = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
    )
    assert resp.status_code in (400, 422)


def test_retry_payment_missing_idempotency_key_returns_400() -> None:
    """Retry-payment without Idempotency-Key header must return 400/422."""
    _setup_cart_and_product(101)

    app.dependency_overrides[get_current_user_id] = lambda: 101

    # First create an order with idempotency
    checkout_resp = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
        headers={"Idempotency-Key": "retry-key-1"},
    )
    assert checkout_resp.status_code == 201
    order_id = checkout_resp.json()["id"]

    # Try retry without idempotency key
    resp = client.post(
        f"/orders/{order_id}/retry-payment",
        json={"payment_method_id": "pm_card_visa"},
    )
    assert resp.status_code in (400, 422)


def test_checkout_replay_returns_same_response() -> None:
    """Replay with same Idempotency-Key must return identical response."""
    _setup_cart_and_product(102)

    app.dependency_overrides[get_current_user_id] = lambda: 102

    key = "replay-key-1"
    body = {"payment_method_id": "pm_card_visa"}

    resp1 = client.post(
        "/orders/checkout",
        json=body,
        headers={"Idempotency-Key": key},
    )
    assert resp1.status_code == 201
    body1 = resp1.json()

    resp2 = client.post(
        "/orders/checkout",
        json=body,
        headers={"Idempotency-Key": key},
    )
    assert resp2.status_code == 201
    body2 = resp2.json()

    assert body1["id"] == body2["id"]
    assert body1["status"] == body2["status"]


def test_checkout_replay_does_not_create_duplicate_orders() -> None:
    """Replay with same Idempotency-Key must not create duplicate orders."""
    _setup_cart_and_product(103)

    app.dependency_overrides[get_current_user_id] = lambda: 103

    key = "replay-key-2"
    body = {"payment_method_id": "pm_card_visa"}

    client.post(
        "/orders/checkout",
        json=body,
        headers={"Idempotency-Key": key},
    )
    client.post(
        "/orders/checkout",
        json=body,
        headers={"Idempotency-Key": key},
    )

    session = SessionLocal()
    order_repo = OrderRepository(session)
    orders = order_repo.get_by_user_id(103)
    session.close()

    assert len(orders) == 1


def test_checkout_replay_does_not_create_duplicate_payments() -> None:
    """Replay with same Idempotency-Key must not create duplicate payments."""
    _setup_cart_and_product(104)

    app.dependency_overrides[get_current_user_id] = lambda: 104

    key = "replay-key-3"
    body = {"payment_method_id": "pm_card_visa"}

    resp1 = client.post(
        "/orders/checkout",
        json=body,
        headers={"Idempotency-Key": key},
    )
    assert resp1.status_code == 201
    order_id = resp1.json()["id"]

    client.post(
        "/orders/checkout",
        json=body,
        headers={"Idempotency-Key": key},
    )

    session = SessionLocal()
    payment_repo = PaymentRepository(session)
    payments = payment_repo.get_by_order_id(order_id)
    session.close()

    assert len(payments) == 1


def test_retry_payment_replay_returns_same_response() -> None:
    """Replay retry-payment with same key returns identical response."""
    _setup_cart_and_product(105)

    app.dependency_overrides[get_current_user_id] = lambda: 105

    key = "retry-replay-key-1"
    body = {"payment_method_id": "pm_card_visa"}

    checkout_resp = client.post(
        "/orders/checkout",
        json=body,
        headers={"Idempotency-Key": key},
    )
    assert checkout_resp.status_code == 201
    order_id = checkout_resp.json()["id"]

    retry_resp1 = client.post(
        f"/orders/{order_id}/retry-payment",
        json=body,
        headers={"Idempotency-Key": key},
    )
    assert retry_resp1.status_code == 200
    body1 = retry_resp1.json()

    retry_resp2 = client.post(
        f"/orders/{order_id}/retry-payment",
        json=body,
        headers={"Idempotency-Key": key},
    )
    assert retry_resp2.status_code == 200
    body2 = retry_resp2.json()

    assert body1["id"] == body2["id"]
    assert body1["status"] == body2["status"]
