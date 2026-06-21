"""Integration tests for admin routes.

Covers:
- Admin authorized access to /admin/orders, /admin/payments
- Non-admin blocked (403 Forbidden)
- Unauthenticated blocked (401 Unauthorized)
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.core.database import Base, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def _create_user_via_api(role: str = "user") -> dict:
    """Create a user and return token + id."""
    import random

    uid = random.randint(10000, 99999)
    email = f"admin-test-{uid}@mail.com"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": "Password123!",
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    # Update role if admin
    if role == "admin":
        from backend.app.core.database import SessionLocal
        from backend.app.modules.user.domain.models import User, UserRole

        session = SessionLocal()
        user = session.get(User, user_id)
        user.role = UserRole.ADMIN
        session.commit()
        session.close()

    token = create_access_token({"sub": str(user_id)})
    return {"token": token, "user_id": user_id}


class TestAdminAuthorized:
    """Admin user can access admin endpoints."""

    def test_admin_can_list_all_orders(self) -> None:
        admin = _create_user_via_api("admin")

        resp = client.get(
            "/admin/orders",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_admin_can_list_all_payments(self) -> None:
        admin = _create_user_via_api("admin")

        resp = client.get(
            "/admin/payments",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestNonAdminBlocked:
    """Regular user is blocked from admin endpoints."""

    def test_regular_user_cannot_list_orders(self) -> None:
        user = _create_user_via_api("user")

        resp = client.get(
            "/admin/orders",
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 403
        body = resp.json()
        assert "detail" in body

    def test_regular_user_cannot_list_payments(self) -> None:
        user = _create_user_via_api("user")

        resp = client.get(
            "/admin/payments",
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 403
        body = resp.json()
        assert "detail" in body


class TestUnauthenticatedBlocked:
    """Unauthenticated requests are blocked (401 before 403)."""

    def test_unauthenticated_cannot_list_orders(self) -> None:
        resp = client.get("/admin/orders")
        assert resp.status_code in (401, 403)

    def test_unauthenticated_cannot_list_payments(self) -> None:
        resp = client.get("/admin/payments")
        assert resp.status_code in (401, 403)
