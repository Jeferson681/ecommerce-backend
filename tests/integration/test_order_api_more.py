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


def test_checkout_returns_404_when_no_cart() -> None:
    session = SessionLocal()

    app.dependency_overrides[get_current_user_id] = lambda: 9999

    def _uow_for(s=session):
        u = UnitOfWork(lambda: s)
        u.attach(s)
        return u

    app.dependency_overrides[get_uow] = lambda: _uow_for()

    resp = client.post("/orders/checkout")
    assert resp.status_code == 404


def test_checkout_returns_400_when_cart_empty() -> None:
    session = SessionLocal()

    cart = Cart(user_id=2)
    session.add(cart)
    session.commit()

    app.dependency_overrides[get_current_user_id] = lambda: 2

    def _uow_for(s=session):
        u = UnitOfWork(lambda: s)
        u.attach(s)
        return u

    app.dependency_overrides[get_uow] = lambda: _uow_for()

    resp = client.post("/orders/checkout")
    assert resp.status_code == 400


def test_checkout_returns_400_on_insufficient_stock() -> None:
    session = SessionLocal()

    product = Product(
        name="P2", description="d", price=Decimal("5.00"), stock_quantity=1
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    cart = Cart(user_id=3)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=5)
    session.add(item)
    session.commit()

    app.dependency_overrides[get_current_user_id] = lambda: 3

    def _uow_for(s=session):
        u = UnitOfWork(lambda: s)
        u.attach(s)
        return u

    app.dependency_overrides[get_uow] = lambda: _uow_for()

    resp = client.post("/orders/checkout")
    assert resp.status_code == 400
