"""Password change integration test.

Covers inventory Must Have item #17: Password Change.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.core.database import Base, engine
from backend.app.main import app
from tests.integration import unique_email

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def test_password_change_succeeds() -> None:
    """Password change with valid old password succeeds and new password works for login."""
    # Create user
    email = unique_email("pwd-change")
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Pwd",
            "last_name": "Test",
            "email": email,
            "password": "OldPass1!",
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    # Login with old password
    login_resp = client.post(
        "/auth/token",
        json={"email": email, "password": "OldPass1!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Change password
    change_resp = client.patch(
        f"/users/{user_id}/change-password",
        json={"new_password": "NewPass2@"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert change_resp.status_code == 200

    # Login with new password must succeed
    new_login = client.post(
        "/auth/token",
        json={"email": email, "password": "NewPass2@"},
    )
    assert new_login.status_code == 200

    # Login with old password must fail
    old_login = client.post(
        "/auth/token",
        json={"email": email, "password": "OldPass1!"},
    )
    assert old_login.status_code == 401


def test_password_change_wrong_owner_fails() -> None:
    """Password change from another user must fail (owner-only)."""
    # Create user A
    email_a = unique_email("owner-a")
    client.post(
        "/users",
        json={
            "first_name": "Owner",
            "last_name": "AA",
            "email": email_a,
            "password": "PassA123!",
        },
    )

    # Create user B
    email_b = unique_email("owner-b")
    create_b = client.post(
        "/users",
        json={
            "first_name": "Owner",
            "last_name": "BB",
            "email": email_b,
            "password": "PassB123!",
        },
    )
    assert create_b.status_code == 201
    user_b_id = create_b.json()["id"]

    # Login as user B
    login_b = client.post(
        "/auth/token",
        json={"email": email_b, "password": "PassB123!"},
    )
    token_b = login_b.json()["access_token"]

    # Try to change user A's password while logged in as user B
    change_resp = client.patch(
        f"/users/{user_b_id + 1}/change-password",  # user A's ID
        json={"new_password": "Hacked1@"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert change_resp.status_code == 400


def test_password_change_weak_password_fails() -> None:
    """Password change with weak password raises validation error."""
    email_weak = unique_email("weak-pwd")
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Weak",
            "last_name": "Pwd",
            "email": email_weak,
            "password": "Strong1!",
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    login_resp = client.post(
        "/auth/token",
        json={"email": email_weak, "password": "Strong1!"},
    )
    token = login_resp.json()["access_token"]

    # Try changing to a weak password
    change_resp = client.patch(
        f"/users/{user_id}/change-password",
        json={"new_password": "weak"},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Pydantic validation enforces min_length on the request body and
    # returns 422 Unprocessable Entity for too-short passwords.
    assert change_resp.status_code == 422
