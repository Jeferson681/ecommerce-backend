from fastapi.testclient import TestClient

from backend.app.core.database import Base, engine
from backend.app.main import app

client = TestClient(app)


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_post_user_creates_and_returns_201():
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        # meet password policy: uppercase, lowercase, digit, special
        "password": "Strong1!",
    }
    resp = client.post("/users", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body


def test_get_user_by_id_returns_user():
    # create user
    payload = {
        "first_name": "Jane",
        "last_name": "Roe",
        "email": "jane@example.com",
        "password": "Another1$",
    }
    resp = client.post("/users", json=payload)
    assert resp.status_code == 201
    user = resp.json()

    login = client.post(
        "/auth/token",
        json={"email": "jane@example.com", "password": "Another1$"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    got = client.get(
        f"/users/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert got.status_code == 200
    body = got.json()
    assert body["email"] == "jane@example.com"
