"""Checkout → Payment flow integration tests.

Validates the full checkout-to-payment pipeline with real database:
- create_payment creates PENDING payment
- checkout creates order + payment
- payment fields are persisted correctly
- retry-payment endpoint
- cart auto-creation on add-item
- cart merge
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token
from backend.app.modules.order.domain.models import Order
from backend.app.modules.payment.domain.models import PaymentStatus
from backend.app.modules.payment.gateway.base import PaymentGatewayResult
from backend.app.modules.payment.gateway.stripe_gateway import StripeGateway
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.domain.models import User, UserRole

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def _create_user(session, email: str, role: str = UserRole.USER) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        password_hash="x",
        role=role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_product(session, price: str = "10.00", stock: int = 10) -> Product:
    product = Product(
        name="Test Product", description="d", price=Decimal(price), stock_quantity=stock
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


class TestCheckoutCreatesPayment:
    """Checkout creates order and payment with correct initial state."""

    def test_checkout_creates_order_and_payment(self) -> None:
        session = SessionLocal()
        user = _create_user(session, "checkout-pay@example.com")
        token = create_access_token({"sub": str(user.id)})
        product = _create_product(session)

        # Cart is auto-created when adding item via API
        resp_add = client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_add.status_code == 201

        # Checkout
        resp = client.post(
            "/orders/checkout",
            json={"payment_method_id": "pm_card_visa"},
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "checkout-pay-flow-1",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        order_id = body["id"]
        assert body["user_id"] == user.id

        # Verify order exists in DB
        session.expire_all()
        order = session.get(Order, order_id)
        assert order is not None
        assert order.status == "paid"  # payment was success

        # Verify payment exists with correct initial state
        from backend.app.modules.order.repositories.order_repository import (
            OrderRepository,
        )

        order_repo = OrderRepository(session)
        order_with_payments = order_repo.get_by_id(order_id)
        assert order_with_payments is not None
        assert len(order_with_payments.payments) == 1
        payment = order_with_payments.payments[0]
        assert payment.status == PaymentStatus.APPROVED
        assert payment.amount == Decimal("20.00")
        assert payment.provider == "stripe"
        assert payment.provider_payment_id is not None

        # Cart should be cleared after checkout
        from backend.app.modules.cart.repositories.cart_repository import (
            CartRepository,
        )

        cart_repo = CartRepository(session)
        fetched_cart = cart_repo.get_by_user_id(user.id)
        assert fetched_cart is None

        session.close()

    def test_checkout_passes_idempotency_key_to_gateway(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify the idempotency key from the request header reaches the gateway.

        Regression guard for BUG-001: the checkout use case must pass the
        idempotency_key to process_payment(), not only to the local idempotency
        repository. Without this, Stripe's PaymentIntent.create() is called
        with idempotency_key=None, creating a double-charge risk.
        """
        captured_keys: list[str | None] = []

        def tracking_process_payment(
            self: StripeGateway,
            *,
            request: object,
            idempotency_key: str | None = None,
        ) -> PaymentGatewayResult:
            captured_keys.append(idempotency_key)
            return PaymentGatewayResult(
                provider_payment_id="pi_captured",
                status=PaymentStatus.APPROVED,
            )

        monkeypatch.setattr(StripeGateway, "process_payment", tracking_process_payment)

        session = SessionLocal()
        user = _create_user(session, "capture-key@example.com")
        token = create_access_token({"sub": str(user.id)})
        product = _create_product(session)
        session.close()

        client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        )

        idem_key = "capture-key-1"
        resp = client.post(
            "/orders/checkout",
            json={"payment_method_id": "pm_card_visa"},
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": idem_key,
            },
        )

        assert resp.status_code == 201
        assert idem_key in captured_keys, (
            f"Expected idempotency_key {idem_key!r} in captured keys: {captured_keys}"
        )
