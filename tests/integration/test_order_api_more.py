from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token
from backend.app.modules.cart.domain.models import Cart, CartItem
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.domain.models import User, UserRole

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def _create_user(session, email: str) -> User:
    user = User(
        first_name="Order",
        last_name="User",
        email=email,
        password_hash="x",
        role=UserRole.USER,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_checkout_returns_404_when_no_cart() -> None:
    session = SessionLocal()

    user = _create_user(session, "order-no-cart@example.com")
    token = create_access_token({"sub": str(user.id)})

    resp = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "order-no-cart-1",
        },
    )
    assert resp.status_code == 404
    session.close()


def test_checkout_returns_400_when_cart_empty() -> None:
    session = SessionLocal()

    user = _create_user(session, "order-empty-cart@example.com")
    token = create_access_token({"sub": str(user.id)})

    cart = Cart(user_id=user.id)
    session.add(cart)
    session.commit()

    resp = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "order-empty-cart-1",
        },
    )
    assert resp.status_code == 400
    session.close()


def test_checkout_returns_400_on_insufficient_stock() -> None:
    session = SessionLocal()

    user = _create_user(session, "order-low-stock@example.com")
    token = create_access_token({"sub": str(user.id)})

    product = Product(
        name="P2", description="d", price=Decimal("5.00"), stock_quantity=1
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    cart = Cart(user_id=user.id)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=5)
    session.add(item)
    session.commit()

    resp = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "order-low-stock-1",
        },
    )
    assert resp.status_code == 400
    session.close()
