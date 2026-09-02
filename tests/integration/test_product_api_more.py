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
    session.close()
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


# =============================================================================
# Pagination
# =============================================================================


def test_list_products_paginated_returns_metadata():
    admin_headers = _admin_headers("admin-pag-meta@example.com")
    for i in range(5):
        resp = client.post(
            "/products",
            json={
                "name": f"Paginated Product {i}",
                "description": "d",
                "price": 1.0,
                "stock_quantity": 10,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201

    resp = client.get("/products", params={"page": 1, "per_page": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert set(body) == {"items", "total", "page", "per_page", "total_pages"}
    assert body["page"] == 1
    assert body["per_page"] == 3
    assert len(body["items"]) == 3
    assert body["total"] >= 5
    assert body["total_pages"] == (body["total"] + 2) // 3


def test_list_products_single_page_param_uses_default_per_page():
    resp = client.get("/products", params={"page": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert body["page"] == 1
    assert body["per_page"] == 24
    assert "items" in body


def test_list_products_paginated_generates_next_page():
    resp = client.get("/products", params={"page": 2, "per_page": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert 0 <= len(body["items"]) <= 3


def test_list_products_paginated_count_respects_filters():
    resp = client.get("/products", params={"q": "shirt", "page": 1, "per_page": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert body["total"] == 1
    assert body["total_pages"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "Blue Shirt"


# =============================================================================
# Price filter (server-side)
# =============================================================================


def _seed_price_products(email: str, token: str) -> None:
    admin_headers = _admin_headers(email)
    for name, price in (
        (f"{token} Alpha", 10.0),
        (f"{token} Beta", 50.0),
        (f"{token} Gamma", 90.0),
    ):
        resp = client.post(
            "/products",
            json={
                "name": name,
                "description": f"{token} product",
                "category": f"price-{token}",
                "price": price,
                "stock_quantity": 5,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201


def test_price_filter_without_pagination_returns_filtered_list():
    _seed_price_products("admin-price-nopag@example.com", "PxNoPag")
    resp = client.get(
        "/products", params={"q": "PxNoPag", "min_price": 20, "max_price": 100}
    )
    assert resp.status_code == 200
    body = resp.json()
    # Non-paginated contract preserved: plain list, price-filtered.
    assert isinstance(body, list)
    assert [item["name"] for item in body] == [
        "PxNoPag Beta",
        "PxNoPag Gamma",
    ]


def test_price_filter_paginated_metadata_respects_price():
    _seed_price_products("admin-price-meta@example.com", "PxMeta")
    resp = client.get(
        "/products",
        params={
            "q": "PxMeta",
            "min_price": 20,
            "max_price": 100,
            "page": 1,
            "per_page": 2,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2  # price filter applied before counting
    assert body["total_pages"] == 1
    assert [item["name"] for item in body["items"]] == [
        "PxMeta Beta",
        "PxMeta Gamma",
    ]


def test_price_filter_paginated_page_two():
    _seed_price_products("admin-price-p2@example.com", "PxPage2")
    resp = client.get(
        "/products",
        params={"q": "PxPage2", "min_price": 0, "page": 2, "per_page": 2},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["total_pages"] == 2
    assert body["page"] == 2
    assert [item["name"] for item in body["items"]] == ["PxPage2 Gamma"]


def test_price_filter_min_only_and_max_only():
    _seed_price_products("admin-price-bounds@example.com", "PxBound")
    min_only = client.get(
        "/products",
        params={"q": "PxBound", "min_price": 50, "page": 1, "per_page": 10},
    ).json()
    assert min_only["total"] == 2
    max_only = client.get(
        "/products",
        params={"q": "PxBound", "max_price": 10, "page": 1, "per_page": 10},
    ).json()
    assert max_only["total"] == 1
    assert max_only["items"][0]["name"] == "PxBound Alpha"


def test_price_filter_combined_with_category():
    _seed_price_products("admin-price-cat@example.com", "PxCat")
    resp = client.get(
        "/products",
        params={
            "category": "price-PxCat",
            "min_price": 0,
            "max_price": 20,
            "page": 1,
            "per_page": 10,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "PxCat Alpha"


def test_price_filter_inverted_range_returns_empty_page():
    _seed_price_products("admin-price-inverted@example.com", "PxInv")
    resp = client.get(
        "/products",
        params={
            "q": "PxInv",
            "min_price": 100,
            "max_price": 5,
            "page": 1,
            "per_page": 10,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["total_pages"] == 0
    assert body["items"] == []


def test_price_filter_rejects_negative_values():
    resp = client.get("/products", params={"min_price": -5})
    assert resp.status_code == 422
    resp = client.get("/products", params={"max_price": -1})
    assert resp.status_code == 422
