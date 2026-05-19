from fastapi.testclient import TestClient

from backend.app.core.database import Base, engine
from backend.app.main import app

client = TestClient(app)


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_post_rejects_invalid_price():
    payload = {"name": "p1", "description": "d", "price": 0, "stock_quantity": 1}
    resp = client.post("/products", json=payload)
    assert resp.status_code == 422


def test_post_rejects_negative_stock():
    payload = {"name": "p1", "description": "d", "price": 1.0, "stock_quantity": -1}
    resp = client.post("/products", json=payload)
    assert resp.status_code == 422


def test_post_rejects_empty_name():
    payload = {"name": "", "description": "d", "price": 1.0, "stock_quantity": 1}
    resp = client.post("/products", json=payload)
    assert resp.status_code == 422


def test_get_product_and_404():
    # create
    payload = {"name": "pget", "description": "d", "price": 2.0, "stock_quantity": 1}
    resp = client.post("/products", json=payload)
    assert resp.status_code == 201
    pid = resp.json()["id"]

    # get existing
    resp2 = client.get(f"/products/{pid}")
    assert resp2.status_code == 200

    # get missing
    resp3 = client.get("/products/999999")
    assert resp3.status_code == 404


def test_get_products_list_empty_and_multiple():
    # ensure clean DB
    # create two
    client.post(
        "/products",
        json={"name": "a", "description": "d", "price": 1.0, "stock_quantity": 1},
    )
    client.post(
        "/products",
        json={"name": "b", "description": "d", "price": 2.0, "stock_quantity": 2},
    )

    resp = client.get("/products")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 2


def test_patch_partial_update_and_delete():
    # create
    payload = {"name": "toupd", "description": "d", "price": 3.0, "stock_quantity": 4}
    r = client.post("/products", json=payload)
    pid = r.json()["id"]

    # partial update (change name only)
    up = {"name": "newname"}
    resp = client.patch(f"/products/{pid}", json=up)
    assert resp.status_code == 200
    assert resp.json()["name"] == "newname"

    # delete
    resp2 = client.delete(f"/products/{pid}")
    assert resp2.status_code == 204

    # ensure 404 after delete
    resp3 = client.get(f"/products/{pid}")
    assert resp3.status_code == 404
