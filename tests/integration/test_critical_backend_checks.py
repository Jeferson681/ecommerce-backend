from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.app.core.database import SessionLocal
from backend.app.main import create_app
from backend.app.modules.auth.tokens import create_access_token
from backend.app.modules.cart.domain.models import CartItem
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.domain.models import User


def _create_user(session, email: str) -> User:
    user = User(first_name="Test", last_name="User", email=email, password_hash="x")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_product(session, name: str, stock: int = 10) -> Product:
    product = Product(name=name, description=None, price=1.0, stock_quantity=stock)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@pytest.mark.integration
def test_ownership_api_protection():
    app = create_app()
    client = TestClient(app)

    session = SessionLocal()
    user_a = _create_user(session, "a@example.com")
    user_b = _create_user(session, "b@example.com")
    product = _create_product(session, "sku-1")

    token_a = create_access_token({"sub": str(user_a.id)})
    token_b = create_access_token({"sub": str(user_b.id)})

    # User A adds an item
    r = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 201
    item = r.json()

    # User B attempts to update that item -> should be NotFound (ownership enforced)
    r2 = client.patch(
        f"/cart/items/{item['id']}",
        json={"quantity": 2},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r2.status_code == 404


@pytest.mark.integration
def test_jwt_missing_malformed_and_expired():
    app = create_app()
    client = TestClient(app)

    session = SessionLocal()
    user = _create_user(session, "jwt@example.com")

    # Missing header
    r = client.get("/cart")
    assert r.status_code == 401

    # Malformed header
    token = create_access_token({"sub": str(user.id)})
    r2 = client.get("/cart", headers={"Authorization": f"Bear {token}"})
    assert r2.status_code == 401

    # Expired token (negative expiry)
    expired = create_access_token({"sub": str(user.id)}, expires_delta=-1)
    r3 = client.get("/cart", headers={"Authorization": f"Bearer {expired}"})
    assert r3.status_code == 401


@pytest.mark.integration
def test_transaction_rollback_on_exception(monkeypatch):
    app = create_app()
    client = TestClient(app)
    session = SessionLocal()

    user = _create_user(session, "tx@example.com")
    product = _create_product(session, "sku-tx", stock=5)

    token = create_access_token({"sub": str(user.id)})

    # Add an item to cart
    r = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201

    # Force an exception during order creation by monkeypatching OrderItemRepository.create
    from backend.app.modules.order.repositories.order_repository import (
        OrderItemRepository,
    )

    def _raise_create(*args: Any, **kwargs: Any):
        raise Exception("boom")

    monkeypatch.setattr(OrderItemRepository, "create", _raise_create)

    # Attempt checkout should fail and rollback: cart should remain and product stock unchanged
    r2 = client.post("/orders/checkout", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 500

    # Verify cart still exists (GET /cart)
    r3 = client.get("/cart", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    cart = r3.json()
    assert cart["items"] and cart["items"][0]["product_id"] == product.id

    # Verify product stock unchanged
    session.refresh(product)
    assert product.stock_quantity == 5


@pytest.mark.integration
def test_concurrent_checkouts_no_oversell():
    app = create_app()
    client = TestClient(app)
    session = SessionLocal()

    # Create product with stock 1
    product = _create_product(session, "sku-concurrent", stock=1)

    # Create two users and give each a cart item for same product
    u1 = _create_user(session, "c1@example.com")
    u2 = _create_user(session, "c2@example.com")
    t1 = create_access_token({"sub": str(u1.id)})
    t2 = create_access_token({"sub": str(u2.id)})

    r = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert r.status_code == 201
    r = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {t2}"},
    )
    assert r.status_code == 201

    def do_checkout(token: str) -> int:
        res = client.post(
            "/orders/checkout", headers={"Authorization": f"Bearer {token}"}
        )
        return res.status_code

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(do_checkout, [t1, t2]))

    # Expect one success (201) and other fail (400/422/500 depending on timing)
    assert 201 in results

    # Ensure product not oversold
    session.refresh(product)
    assert product.stock_quantity >= 0


@pytest.mark.integration
def test_idempotency_risk_duplicate_orders():
    app = create_app()
    client = TestClient(app)
    session = SessionLocal()

    user = _create_user(session, "ido@example.com")
    product = _create_product(session, "sku-ido", stock=10)
    token = create_access_token({"sub": str(user.id)})

    # Add item
    r = client.post(
        "/cart/items",
        json={"product_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201

    # Call checkout twice (simulating a retry) -- current system doesn't implement idempotency
    r1 = client.post("/orders/checkout", headers={"Authorization": f"Bearer {token}"})
    r2 = client.post("/orders/checkout", headers={"Authorization": f"Bearer {token}"})

    # At least the first should succeed
    assert r1.status_code == 201

    # The second may succeed or fail depending on state; the test documents the behavior (risk)
    assert r2.status_code in (201, 400, 404, 500)


@pytest.mark.integration
def test_repository_pagination_edge_case():
    # Test UserRepository.list pagination boundaries
    from backend.app.modules.user.repositories.user_repository import UserRepository

    session = SessionLocal()
    repo = UserRepository(session)

    # Create 3 users
    emails = [f"p{i}@example.com" for i in range(3)]
    for e in emails:
        _create_user(session, e)

    all_users = repo.list(limit=2, offset=0)
    assert len(all_users) == 2
    next_page = repo.list(limit=2, offset=2)
    assert len(next_page) >= 1


@pytest.mark.integration
def test_db_constraint_unique_cart_item():
    session = SessionLocal()

    # create user, product and cart

    user = _create_user(session, "unique@example.com")
    product = _create_product(session, "sku-unique")

    # Better: construct a Cart ORM instance directly
    from backend.app.modules.cart.domain.models import Cart

    cart = Cart(user_id=user.id)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    # Add same cart+product twice to violate unique constraint
    ci1 = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    ci2 = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    session.add(ci1)
    session.commit()
    session.add(ci2)
    with pytest.raises(IntegrityError):
        session.commit()
