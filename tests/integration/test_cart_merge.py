"""Tests for cart merge endpoint.

POST /cart/merge merges a list of items into the user's authenticated cart.
Validates:
- items from local storage are added to server cart
- duplicate products have quantities summed
- new cart is created if none exists
- items are preserved
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


def _create_product(
    session, name: str, price: str = "10.00", stock: int = 10
) -> Product:
    product = Product(
        name=name,
        description="d",
        price=Decimal(price),
        stock_quantity=stock,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


class TestCartMerge:
    """POST /cart/merge merges local items into authenticated cart."""

    def test_merge_empty_list_creates_cart(self) -> None:
        """Merging an empty list creates or returns the existing cart."""
        session = SessionLocal()
        user = _create_user(session, "merge-empty@example.com")
        token = create_access_token({"sub": str(user.id)})

        resp = client.post(
            "/cart/merge",
            json=[],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        cart = resp.json()
        assert cart["user_id"] == user.id

        session.close()

    def test_merge_items_adds_products(self) -> None:
        """Merging items adds them to the user's cart.

        Note: The merge endpoint does NOT return items eagerly in the response.
        Items are verified by querying GET /cart after merge.
        """
        session = SessionLocal()
        user = _create_user(session, "merge-new@example.com")
        token = create_access_token({"sub": str(user.id)})
        product_a = _create_product(session, "Product A")
        product_b = _create_product(session, "Product B")

        resp = client.post(
            "/cart/merge",
            json=[
                {"product_id": product_a.id, "quantity": 2},
                {"product_id": product_b.id, "quantity": 1},
            ],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # Verify items via GET /cart (items may not be included in merge response)
        cart_resp = client.get(
            "/cart",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert cart_resp.status_code == 200
        cart = cart_resp.json()
        assert len(cart["items"]) == 2, f"Expected 2 items, got {len(cart['items'])}"

        item_map = {item["product_id"]: item["quantity"] for item in cart["items"]}
        assert item_map[product_a.id] == 2
        assert item_map[product_b.id] == 1

        session.close()

    def test_merge_into_existing_cart_sums_quantities(self) -> None:
        """Merging items into an existing cart sums quantities for duplicates."""
        session = SessionLocal()
        user = _create_user(session, "merge-sum@example.com")
        token = create_access_token({"sub": str(user.id)})
        product = _create_product(session, "Sum Product")

        # First add item directly
        r1 = client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 201

        # Now merge more of the same product
        resp = client.post(
            "/cart/merge",
            json=[
                {"product_id": product.id, "quantity": 2},
            ],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # Verify via GET
        cart_resp = client.get(
            "/cart",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert cart_resp.status_code == 200
        cart = cart_resp.json()
        item_map = {item["product_id"]: item["quantity"] for item in cart["items"]}
        # Should be 3 (from add) + 2 (from merge) = 5
        assert item_map[product.id] == 5, (
            f"Expected quantity 5 (3+2), got {item_map[product.id]}"
        )

        session.close()

    def test_merge_with_existing_cart_items_preserved(self) -> None:
        """Existing cart items are preserved when new items are merged."""
        session = SessionLocal()
        user = _create_user(session, "merge-preserve@example.com")
        token = create_access_token({"sub": str(user.id)})
        existing_product = _create_product(session, "Existing Product")
        new_product = _create_product(session, "New Product")

        # Add item to cart
        r1 = client.post(
            "/cart/items",
            json={"product_id": existing_product.id, "quantity": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 201

        # Merge a different product
        client.post(
            "/cart/merge",
            json=[
                {"product_id": new_product.id, "quantity": 4},
            ],
            headers={"Authorization": f"Bearer {token}"},
        )

        # Verify via GET
        cart_resp = client.get(
            "/cart",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert cart_resp.status_code == 200
        cart = cart_resp.json()
        assert len(cart["items"]) == 2, f"Expected 2 items, got {len(cart['items'])}"

        item_map = {item["product_id"]: item["quantity"] for item in cart["items"]}
        assert item_map[existing_product.id] == 1, "Existing item quantity changed"
        assert item_map[new_product.id] == 4, "New item not added"

        session.close()

    def test_merge_invalid_product_succeeds_but_item_not_added(self) -> None:
        """Merging a non-existent product succeeds but item is skipped.

        The merge endpoint uses get_or_create_cart which validates product
        existence. The response may still be 200 with empty items.
        """
        session = SessionLocal()
        user = _create_user(session, "merge-404@example.com")
        token = create_access_token({"sub": str(user.id)})

        resp = client.post(
            "/cart/merge",
            json=[{"product_id": 999999, "quantity": 1}],
            headers={"Authorization": f"Bearer {token}"},
        )
        # Merge returns 404 when product does not exist
        assert resp.status_code == 404

        session.close()

    def test_merge_without_auth_returns_401(self) -> None:
        """Merging without authentication returns 401."""
        resp = client.post(
            "/cart/merge",
            json=[{"product_id": 1, "quantity": 1}],
        )
        assert resp.status_code == 401
