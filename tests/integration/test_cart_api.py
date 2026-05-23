from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.api.routers.cart import get_current_user_id, get_uow
from backend.app.application.uow.unit_of_work import UnitOfWork
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.product.domain.models import Product

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def _override_auth_and_uow(user_id: int, session):
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    app.dependency_overrides[get_uow] = lambda: UnitOfWork(session)


def test_post_cart_items_adds_item_and_get_cart_returns_cart() -> None:
    session = SessionLocal()
    product = Product(
        name="Produto API", description="d", price=Decimal("10.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    _override_auth_and_uow(user_id=1, session=session)

    add_resp = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 2},
    )

    assert add_resp.status_code == 201
    body = add_resp.json()
    assert body["product_id"] == product.id
    assert body["quantity"] == 2

    cart_resp = client.get("/cart")
    assert cart_resp.status_code == 200
    cart = cart_resp.json()
    assert cart["user_id"] == 1
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == product.id


def test_patch_and_delete_cart_item() -> None:
    session = SessionLocal()
    product = Product(
        name="Produto API 2", description="d", price=Decimal("12.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    _override_auth_and_uow(user_id=2, session=session)

    add_resp = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
    )
    assert add_resp.status_code == 201
    item_id = add_resp.json()["id"]

    patch_resp = client.patch(f"/cart/items/{item_id}", json={"quantity": 5})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["quantity"] == 5

    delete_resp = client.delete(f"/cart/items/{item_id}")
    assert delete_resp.status_code == 204

    session.expire_all()
    cart_resp = client.get("/cart")
    assert cart_resp.status_code == 200
    assert cart_resp.json()["items"] == []


def test_patch_and_delete_missing_cart_item_returns_404() -> None:
    session = SessionLocal()
    product = Product(
        name="Produto API 3", description="d", price=Decimal("13.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()

    _override_auth_and_uow(user_id=3, session=session)

    patch_resp = client.patch("/cart/items/999999", json={"quantity": 5})
    assert patch_resp.status_code == 404

    delete_resp = client.delete("/cart/items/999999")
    assert delete_resp.status_code == 404
