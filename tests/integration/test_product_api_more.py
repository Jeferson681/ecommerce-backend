from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token
from backend.app.modules.user.domain.models import User, UserRole

client = TestClient(app)


def _admin_headers(email: str = "admin-product-more@example.com") -> dict[str, str]:
    session = SessionLocal()
    admin = User(
        first_name="Admin",
        last_name="User",
        email=email,
        password_hash="x",
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    token = create_access_token({"sub": str(admin.id)})
    return {"Authorization": f"Bearer {token}"}


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_post_rejects_invalid_price():
    payload = {"name": "p1", "description": "d", "price": 0, "stock_quantity": 1}
    resp = client.post(
        "/products", json=payload, headers=_admin_headers("admin1@example.com")
    )
    assert resp.status_code == 422


def test_post_rejects_negative_stock():
    payload = {"name": "p1", "description": "d", "price": 1.0, "stock_quantity": -1}
    resp = client.post(
        "/products", json=payload, headers=_admin_headers("admin2@example.com")
    )
    assert resp.status_code == 422


def test_post_rejects_empty_name():
    payload = {"name": "", "description": "d", "price": 1.0, "stock_quantity": 1}
    resp = client.post(
        "/products", json=payload, headers=_admin_headers("admin3@example.com")
    )
    assert resp.status_code == 422


def test_get_product_and_404():
    # create
    payload = {"name": "pget", "description": "d", "price": 2.0, "stock_quantity": 1}
    resp = client.post(
        "/products", json=payload, headers=_admin_headers("admin4@example.com")
    )
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
    admin_headers = _admin_headers("admin5@example.com")
    client.post(
        "/products",
        json={"name": "a", "description": "d", "price": 1.0, "stock_quantity": 1},
        headers=admin_headers,
    )
    client.post(
        "/products",
        json={"name": "b", "description": "d", "price": 2.0, "stock_quantity": 2},
        headers=admin_headers,
    )

    resp = client.get("/products")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 2


def test_patch_partial_update_and_delete():
    # create
    admin_headers = _admin_headers("admin6@example.com")
    payload = {"name": "toupd", "description": "d", "price": 3.0, "stock_quantity": 4}
    r = client.post("/products", json=payload, headers=admin_headers)
    pid = r.json()["id"]

    # partial update (change name only)
    up = {"name": "newname"}
    resp = client.patch(f"/products/{pid}", json=up, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "newname"

    # delete
    resp2 = client.delete(f"/products/{pid}", headers=admin_headers)
    assert resp2.status_code == 204

    # ensure 404 after delete
    resp3 = client.get(f"/products/{pid}")
    assert resp3.status_code == 404


def test_get_products_supports_query_category_and_sort():
    admin_headers = _admin_headers("admin-query@example.com")

    client.post(
        "/products",
        json={
            "name": "Blue Shirt",
            "description": "cotton shirt",
            "category": "clothes",
            "price": 25.0,
            "stock_quantity": 3,
        },
        headers=admin_headers,
    )
    client.post(
        "/products",
        json={
            "name": "Black Pants",
            "description": "formal pants",
            "category": "clothes",
            "price": 40.0,
            "stock_quantity": 2,
        },
        headers=admin_headers,
    )
    client.post(
        "/products",
        json={
            "name": "Coffee Mug",
            "description": "home item",
            "category": "home",
            "price": 10.0,
            "stock_quantity": 6,
        },
        headers=admin_headers,
    )

    search_resp = client.get("/products", params={"q": "shirt"})
    assert search_resp.status_code == 200
    assert len(search_resp.json()) == 1
    assert search_resp.json()[0]["name"] == "Blue Shirt"

    filter_resp = client.get("/products", params={"category": "clothes"})
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) == 2

    sort_resp = client.get("/products", params={"sort": "price_desc"})
    assert sort_resp.status_code == 200
    prices = [Decimal(item["price"]) for item in sort_resp.json()]
    assert prices == sorted(prices, reverse=True)

    composed_resp = client.get(
        "/products",
        params={"q": "shirt", "category": "clothes", "sort": "price_asc"},
    )
    assert composed_resp.status_code == 200
    assert len(composed_resp.json()) == 1
    assert composed_resp.json()[0]["name"] == "Blue Shirt"
