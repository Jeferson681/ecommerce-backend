"""Tests for idempotency key release on checkout failure.

The checkout use case commits the idempotency claim before processing payment.
If the Stripe gateway raises an exception (e.g. missing STRIPE_SECRET_KEY),
the exception propagates up, but the idempotency key remains in "in progress"
state (response_status=None) permanently.

This test suite verifies the fix: after a failed checkout, the same
idempotency key must be usable for a new attempt (either released or
allowed to retry).
"""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.domain.models import User, UserRole

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def _create_user(session, email: str) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        password_hash="x",
        role=UserRole.USER,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_product(session, stock: int = 10) -> Product:
    product = Product(
        name="Test Product",
        description="d",
        price=Decimal("10.00"),
        stock_quantity=stock,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


class TestIdempotencyReleaseOnFailure:
    """Idempotency key must be releasable after a failed checkout."""

    def test_idempotency_released_after_gateway_error(self) -> None:
        """After checkout failure, the idempotency key is released for retry."""
        session = SessionLocal()
        user = _create_user(session, "idem-release@example.com")
        token = create_access_token({"sub": str(user.id)})
        product = _create_product(session)

        # Add item to cart
        r = client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201

        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "release-key-1",
        }

        # First checkout attempt — fails (no Stripe key configured)
        client.post(
            "/orders/checkout",
            json={"payment_method_id": "pm_card_visa"},
            headers=headers,
        )

        # Second attempt with SAME key — must NOT be stuck
        r2 = client.post(
            "/orders/checkout",
            json={"payment_method_id": "pm_card_visa"},
            headers=headers,
        )

        # The key was released after the first failure, so the second attempt
        # must NOT return "Idempotent request already in progress"
        assert (
            r2.status_code != 400
        ), f"Idempotency key should have been released. Got {r2.status_code}: {r2.text[:200]}"

        session.close()
