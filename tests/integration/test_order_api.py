from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.api.routers.order import get_current_user_id, get_uow
from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.cart.domain.models import Cart, CartItem
from backend.app.modules.product.domain.models import Product

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def _create_product(session, price="10.00"):
    product = Product(
        name="P", description="d", price=Decimal(price), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def test_checkout_endpoint_creates_order_and_clears_cart() -> None:
    session = SessionLocal()

    product = _create_product(session)

    cart = Cart(user_id=1)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=2)
    session.add(item)
    session.commit()

    app.dependency_overrides[get_current_user_id] = lambda: 1
    app.dependency_overrides[get_uow] = lambda: UnitOfWork(session)

    resp = client.post("/orders/checkout")
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_id"] == 1

    # cart should be cleared
    session.expire_all()
    from backend.app.modules.cart.repositories.cart_repository import (
        CartRepository,
    )

    cart_repo = CartRepository(session)
    fetched = cart_repo.get_by_user_id(1)
    assert fetched is None
