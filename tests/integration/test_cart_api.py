"""Integration tests for cart API with real auth flow."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.product.domain.models import Product
from tests.integration import unique_email

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def _create_user_and_login() -> dict:
    """Create user and return auth token."""
    email = unique_email("cart")
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Cart",
            "last_name": "Tester",
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
    return {"token": token, "user_id": user_id}


def test_post_cart_items_adds_item_and_get_cart_returns_cart() -> None:
    session = SessionLocal()
    product = Product(
        name="Produto API", description="d", price=Decimal("10.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    session.close()

    user = _create_user_and_login()

    add_resp = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 2},
        headers={"Authorization": f"Bearer {user['token']}"},
    )

    assert add_resp.status_code == 201
    body = add_resp.json()
    assert body["product_id"] == product.id
    assert body["quantity"] == 2

    cart_resp = client.get(
        "/cart",
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert cart_resp.status_code == 200
    cart = cart_resp.json()
    assert cart["user_id"] == user["user_id"]
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
    session.close()

    user = _create_user_and_login()

    add_resp = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert add_resp.status_code == 201
    item_id = add_resp.json()["id"]

    patch_resp = client.patch(
        f"/cart/items/{item_id}",
        json={"quantity": 5},
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["quantity"] == 5

    delete_resp = client.delete(
        f"/cart/items/{item_id}",
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert delete_resp.status_code == 204

    cart_resp = client.get(
        "/cart",
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert cart_resp.status_code == 200
    assert cart_resp.json()["items"] == []


def test_patch_and_delete_missing_cart_item_returns_404() -> None:
    user = _create_user_and_login()

    patch_resp = client.patch(
        "/cart/items/999999",
        json={"quantity": 5},
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert patch_resp.status_code == 404

    delete_resp = client.delete(
        "/cart/items/999999",
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert delete_resp.status_code == 404


def test_patch_cart_item_quantity_exceeding_stock_returns_400() -> None:
    """Regression: PATCH quantity must be validated against available stock."""
    session = SessionLocal()
    product = Product(
        name="Produto API 3", description="d", price=Decimal("9.00"), stock_quantity=3
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    session.close()

    user = _create_user_and_login()
    headers = {"Authorization": f"Bearer {user['token']}"}

    add_resp = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=headers,
    )
    assert add_resp.status_code == 201
    item_id = add_resp.json()["id"]

    patch_resp = client.patch(
        f"/cart/items/{item_id}",
        json={"quantity": 10},
        headers=headers,
    )
    assert patch_resp.status_code == 400

    # Quantity must remain unchanged after the rejected update
    cart_resp = client.get("/cart", headers=headers)
    assert cart_resp.status_code == 200
    items = cart_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["quantity"] == 1


def test_patch_cart_item_quantity_up_to_stock_succeeds() -> None:
    """Updating to a quantity equal to the available stock is allowed."""
    session = SessionLocal()
    product = Product(
        name="Produto API 4", description="d", price=Decimal("9.00"), stock_quantity=4
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    session.close()

    user = _create_user_and_login()
    headers = {"Authorization": f"Bearer {user['token']}"}

    add_resp = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=headers,
    )
    assert add_resp.status_code == 201
    item_id = add_resp.json()["id"]

    patch_resp = client.patch(
        f"/cart/items/{item_id}",
        json={"quantity": 4},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["quantity"] == 4


def test_delete_cart_clears_all_items() -> None:
    """DELETE /cart must remove the server cart and all of its items."""
    session = SessionLocal()
    product = Product(
        name="Produto API 5", description="d", price=Decimal("7.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    session.close()

    user = _create_user_and_login()
    headers = {"Authorization": f"Bearer {user['token']}"}

    add_resp = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 2},
        headers=headers,
    )
    assert add_resp.status_code == 201

    delete_resp = client.delete("/cart", headers=headers)
    assert delete_resp.status_code == 204

    # The cart no longer exists on the server
    cart_resp = client.get("/cart", headers=headers)
    assert cart_resp.status_code == 404

    # A new cart can be created afterwards
    add_resp = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers=headers,
    )
    assert add_resp.status_code == 201


def test_delete_cart_without_existing_cart_returns_404() -> None:
    user = _create_user_and_login()

    delete_resp = client.delete(
        "/cart",
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert delete_resp.status_code == 404
