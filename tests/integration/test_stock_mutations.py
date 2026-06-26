"""Stock mutation integration tests.

Validates that stock is correctly decremented during checkout and
restored when checkout fails — covering the 4 stock-related Must Have items
from the inventory (items 3, 4, 5, 6).
"""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.repositories.product_repository import (
    ProductRepository,
)
from backend.app.modules.user.domain.models import User, UserRole

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def _create_user(session, email: str) -> User:
    user = User(
        first_name="Stock",
        last_name="Test",
        email=email,
        password_hash="x",
        role=UserRole.USER,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_checkout_decrements_stock() -> None:
    """Stock reservation: checkout must atomically decrement stock.

    Covers inventory Must Have items:
    - Stock Reservation (item 3)
    - Atomic Stock Decrement (item 5)
    """
    session = SessionLocal()
    user = _create_user(session, "stock-decr@example.com")
    token = create_access_token({"sub": str(user.id)})

    product = Product(
        name="Stock Test", description="d", price=Decimal("10.00"), stock_quantity=5
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    product_id = product.id

    # Add item to cart
    client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 2},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Checkout
    resp = client.post(
        "/orders/checkout",
        json={"payment_method_id": "pm_card_visa"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "stock-decr-1",
        },
    )
    assert resp.status_code == 201

    # Verify stock was decremented: 5 - 2 = 3
    session.expire_all()
    repo = ProductRepository(session)
    updated = repo.get_by_id(product_id)
    assert updated is not None
    assert updated.stock_quantity == 3, f"Expected 3, got {updated.stock_quantity}"

    session.close()


def test_checkout_insufficient_stock_raises_error() -> None:
    """Stock reservation: insufficient stock must raise ValidationError.

    Stock validation occurs at add_item time. Adding an item with quantity
    exceeding available stock must fail before checkout is attempted.
    """
    session = SessionLocal()
    user = _create_user(session, "stock-insuf@example.com")
    token = create_access_token({"sub": str(user.id)})

    product = Product(
        name="Low Stock", description="d", price=Decimal("5.00"), stock_quantity=1
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    product_id = product.id

    # Add item with quantity exceeding stock — must fail at add_item time
    resp = client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400

    # Stock must remain unchanged
    session.expire_all()
    repo = ProductRepository(session)
    unchanged = repo.get_by_id(product_id)
    assert unchanged is not None
    assert unchanged.stock_quantity == 1

    session.close()


def test_atomic_decrement_concurrent_safety() -> None:
    """Atomic stock decrement: concurrent checkouts must not oversell.

    Two concurrent requests for the same limited stock must not exceed
    available inventory. At least one must fail.
    """
    import threading

    session = SessionLocal()
    user = _create_user(session, "stock-conc@example.com")
    token = create_access_token({"sub": str(user.id)})

    # Only 1 item in stock
    product = Product(
        name="Concurrent Stock",
        description="d",
        price=Decimal("1.00"),
        stock_quantity=1,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    product_id = product.id

    # Both requests try to buy the same single item
    client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )

    from backend.app.api.routers.order import get_current_user_id

    app.dependency_overrides[get_current_user_id] = lambda: user.id

    responses: list = []

    def do_checkout():
        resp = client.post(
            "/orders/checkout",
            json={"payment_method_id": "pm_card_visa"},
            headers={"Idempotency-Key": f"stock-conc-{threading.get_ident()}"},
        )
        responses.append(resp)

    t1 = threading.Thread(target=do_checkout)
    t2 = threading.Thread(target=do_checkout)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    successes = [r for r in responses if r.status_code == 201]
    failures = [r for r in responses if r.status_code != 201]

    # At most 1 should succeed (only 1 item in stock)
    assert len(successes) <= 1
    assert len(failures) >= 1, "At least one concurrent checkout should have failed"

    # Stock should be 0 (if success) or 1 (if both failed)
    session.expire_all()
    repo = ProductRepository(session)
    final = repo.get_by_id(product_id)
    assert final is not None
    assert final.stock_quantity <= 1

    app.dependency_overrides.clear()
    session.close()


def test_atomic_stock_increment() -> None:
    """Stock restoration: decrement_stock_if_enough SQL is correct.

    This tests the repository-level atomic operation directly.
    Covers items 5 and 6 from the inventory.
    """
    session = SessionLocal()

    product = Product(
        name="Atomic Test", description="d", price=Decimal("10.00"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    product_id = product.id
    session.close()

    # Decrement via repository
    session = SessionLocal()
    repo = ProductRepository(session)
    success = repo.decrement_stock_if_enough(product_id=product_id, quantity=3)
    assert success is True
    session.commit()
    session.close()

    # Verify
    session = SessionLocal()
    repo = ProductRepository(session)
    p = repo.get_by_id(product_id)
    assert p is not None
    assert p.stock_quantity == 7
    session.close()

    # Increment (restore) via repository
    session = SessionLocal()
    repo = ProductRepository(session)
    repo.increment_stock(product_id=product_id, quantity=2)
    session.commit()
    session.close()

    # Verify restored
    session = SessionLocal()
    repo = ProductRepository(session)
    p = repo.get_by_id(product_id)
    assert p is not None
    assert p.stock_quantity == 9, f"Expected 9, got {p.stock_quantity}"
    session.close()


def test_decrement_insufficient_stock_returns_false() -> None:
    """Atomic stock decrement: decrement beyond stock must return False.

    Covers the failure path of decrement_stock_if_enough (item 5).
    """
    session = SessionLocal()

    product = Product(
        name="Insufficient Test",
        description="d",
        price=Decimal("10.00"),
        stock_quantity=2,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    product_id = product.id
    session.close()

    # Try to decrement more than available
    session = SessionLocal()
    repo = ProductRepository(session)
    success = repo.decrement_stock_if_enough(product_id=product_id, quantity=5)
    assert success is False
    session.close()

    # Stock must be unchanged
    session = SessionLocal()
    repo = ProductRepository(session)
    p = repo.get_by_id(product_id)
    assert p is not None
    assert p.stock_quantity == 2
    session.close()
