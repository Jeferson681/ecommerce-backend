from fastapi.testclient import TestClient

from backend.app.core.database import Base, engine
from backend.app.main import app

client = TestClient(app)


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_get_user_not_found_returns_404():
    create_user = client.post(
        "/users",
        json={
            "first_name": "Token",
            "last_name": "User",
            "email": "token-user@example.com",
            "password": "Password123!",
        },
    )
    assert create_user.status_code == 201

    login = client.post(
        "/auth/token",
        json={"email": "token-user@example.com", "password": "Password123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    resp = client.get(
        "/users/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_post_user_invalid_payload_returns_422():
    payload = {
        "first_name": "a",
        "last_name": "b",
        "email": "not-an-email",
        "password": "short",
    }
    resp = client.post("/users", json=payload)
    assert resp.status_code == 422
