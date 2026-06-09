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


def _create_product(session, price="10.00"):
    product = Product(
        name="P", description="d", price=Decimal(price), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


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


def test_checkout_endpoint_creates_order_and_clears_cart() -> None:
    session = SessionLocal()

    user = _create_user(session, "order-checkout@example.com")
    token = create_access_token({"sub": str(user.id)})

    product = _create_product(session)

    cart = Cart(user_id=user.id)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=2)
    session.add(item)
    session.commit()

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
    assert body["user_id"] == user.id

    # cart should be cleared
    session.expire_all()
    from backend.app.modules.cart.repositories.cart_repository import (
        CartRepository,
    )

    cart_repo = CartRepository(session)
    fetched = cart_repo.get_by_user_id(user.id)
    assert fetched is None
