"""Tests for order API with real DB validation."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.cart.domain.models import Cart, CartItem
from backend.app.modules.order.domain.models import Order
from backend.app.modules.payment.repositories.payment_repository import (
    PaymentRepository,
)
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.domain.models import User, UserRole
from tests.integration import unique_email

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def test_checkout_endpoint_creates_order_and_clears_cart() -> None:
    session = SessionLocal()

    user = User(
        first_name="Order",
        last_name="User",
        email=unique_email("order"),
        password_hash="x",
        role=UserRole.USER,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    product = Product(
        name="P", description="d", price=Decimal("10.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    cart = Cart(user_id=user.id)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=2)
    session.add(item)
    session.commit()
    session.close()

    # Login via real auth endpoint
    login_resp = client.post(
        "/auth/token",
        json={"email": user.email, "password": "Password123!"},
    )
    # User was created with password_hash="x" so we use that
    # Actually create via API to ensure password is correct
    session = SessionLocal()
    session.query(CartItem).delete()
    session.query(Cart).delete()
    session.query(Product).delete()
    session.query(User).delete()
    session.commit()
    session.close()

    # Create user via real API so password is hashed correctly
    email = unique_email("order2")
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Order",
            "last_name": "User",
            "email": email,
            "password": "Password123!",
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    login_resp = client.post(
        "/auth/token",
        json={"email": email, "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Create product + cart via DB (products have no auth)
    session = SessionLocal()
    product = Product(
        name="P", description="d", price=Decimal("10.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    cart = Cart(user_id=user_id)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=2)
    session.add(item)
    session.commit()
    session.close()

    resp = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "order-checkout-1",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_id"] == user_id

    # Verify order persists in DB
    order_id = body["id"]
    session = SessionLocal()
    order = session.get(Order, order_id)
    assert order is not None, "Order was not persisted to DB"
    assert order.user_id == user_id

    # Verify payment exists for this order
    pay_repo = PaymentRepository(session)
    payments = pay_repo.get_by_order_id(order_id)
    assert len(payments) == 1, f"Expected 1 payment, got {len(payments)}"
    assert payments[0].order_id == order_id

    # Verify cart is cleared
    from backend.app.modules.cart.repositories.cart_repository import (
        CartRepository,
    )

    cart_repo = CartRepository(session)
    fetched = cart_repo.get_by_user_id(user_id)
    assert fetched is None, "Cart was not cleared after checkout"

    session.close()
