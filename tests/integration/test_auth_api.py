from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_module(module: object) -> None:
    """Create all tables before running tests."""
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    """Drop all tables after running tests."""
    Base.metadata.drop_all(bind=engine)


def test_post_auth_token_with_valid_credentials() -> None:
    """Test login endpoint with valid credentials."""
    # Create a test user via API endpoint
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Ana",
            "last_name": "Silva",
            "email": "ana@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201

    payload = {"email": "ana@mail.com", "password": test_password}
    resp = client.post("/auth/token", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] is not None


def test_post_auth_token_with_invalid_email() -> None:
    """Test login endpoint with non-existent email."""
    payload = {"email": "nonexistent@mail.com", "password": "Password123!"}
    resp = client.post("/auth/token", json=payload)

    assert resp.status_code == 401
    assert "detail" in resp.json() or "message" in resp.json()


def test_post_auth_token_with_invalid_password() -> None:
    """Test login endpoint with incorrect password."""
    # Create a test user via API endpoint
    create_resp = client.post(
        "/users",
        json={
            "first_name": "João",
            "last_name": "Santos",
            "email": "joao@mail.com",
            "password": "Password123!",
        },
    )
    assert create_resp.status_code == 201

    payload = {"email": "joao@mail.com", "password": "WrongPassword"}
    resp = client.post("/auth/token", json=payload)

    assert resp.status_code == 401


def test_post_auth_logout_with_valid_token() -> None:
    """Test logout endpoint with valid refresh token."""
    # First, login to get a refresh token
    # Create user via API and login
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Maria",
            "last_name": "Costa",
            "email": "maria@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201

    login_payload = {"email": "maria@mail.com", "password": test_password}
    login_resp = client.post("/auth/token", json=login_payload)
    assert login_resp.status_code == 200

    refresh_token = login_resp.json()["refresh_token"]

    logout_payload = {"refresh_token": refresh_token}
    logout_resp = client.post("/auth/logout", json=logout_payload)

    assert logout_resp.status_code == 204


def test_post_auth_logout_with_invalid_token() -> None:
    """Test logout endpoint with invalid refresh token."""
    payload = {"refresh_token": "invalid_token_12345"}
    resp = client.post("/auth/logout", json=payload)

    assert resp.status_code == 422 or resp.status_code == 401


def test_post_auth_refresh_with_valid_token() -> None:
    """Test refresh endpoint with valid refresh token."""
    # Create user and login to get tokens
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Carlos",
            "last_name": "Oliveira",
            "email": "carlos@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201

    login_payload = {"email": "carlos@mail.com", "password": test_password}
    login_resp = client.post("/auth/token", json=login_payload)
    assert login_resp.status_code == 200

    refresh_token = login_resp.json()["refresh_token"]

    # Refresh the access token
    refresh_payload = {"refresh_token": refresh_token}
    refresh_resp = client.post("/auth/refresh", json=refresh_payload)

    assert refresh_resp.status_code == 200
    body = refresh_resp.json()
    assert "access_token" in body
    assert body["refresh_token"] == refresh_token
    assert body["token_type"] == "bearer"
    assert body["expires_in"] is not None


def test_post_auth_refresh_with_invalid_token() -> None:
    """Test refresh endpoint with invalid refresh token."""
    payload = {"refresh_token": "invalid_refresh_token"}
    resp = client.post("/auth/refresh", json=payload)

    assert resp.status_code == 401


def test_get_users_me_with_valid_token() -> None:
    """Test GET /users/me endpoint with valid access token."""
    # Create user and login
    test_password = "Password123!"
    create_resp = client.post(
        "/users",
        json={
            "first_name": "Patricia",
            "last_name": "Lima",
            "email": "patricia@mail.com",
            "password": test_password,
        },
    )
    assert create_resp.status_code == 201
    created_user = create_resp.json()
    created_user_id = created_user["id"]

    login_payload = {"email": "patricia@mail.com", "password": test_password}
    login_resp = client.post("/auth/token", json=login_payload)
    assert login_resp.status_code == 200

    access_token = login_resp.json()["access_token"]

    # Call GET /users/me with valid token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = client.get("/users/me", headers=headers)

    assert me_resp.status_code == 200
    body = me_resp.json()
    assert body["id"] == created_user_id
    assert body["email"] == "patricia@mail.com"
    assert body["first_name"] == "Patricia"
    assert body["last_name"] == "Lima"


def test_get_users_me_without_token() -> None:
    """Test GET /users/me endpoint without authorization header."""
    resp = client.get("/users/me")

    assert resp.status_code == 401


def test_get_users_me_with_invalid_token() -> None:
    """Test GET /users/me endpoint with invalid access token."""
    headers = {"Authorization": "Bearer invalid_access_token"}
    resp = client.get("/users/me", headers=headers)

    assert resp.status_code == 401
