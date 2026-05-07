from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_post_products_creates_and_returns_201():
    payload = {"name": "p1", "description": "d", "price": 9.99, "stock_quantity": 5}
    resp = client.post("/products", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
