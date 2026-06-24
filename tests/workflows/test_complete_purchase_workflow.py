from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.auth.tokens import create_access_token
from backend.app.modules.user.domain.models import User, UserRole


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _admin_headers() -> dict[str, str]:
    session = SessionLocal()

    admin = User(
        first_name="Admin",
        last_name="Workflow",
        email=_unique_email("admin"),
        password_hash="seeded-admin",
        role=UserRole.ADMIN,
    )

    session.add(admin)
    session.commit()
    session.refresh(admin)

    token = create_access_token({"sub": str(admin.id)})

    session.close()

    return {"Authorization": f"Bearer {token}"}


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def test_complete_purchase_workflow() -> None:
    """
    Workflow:

    Register
    -> Login
    -> Create Product
    -> Add To Cart
    -> View Cart
    -> Checkout
    -> Retrieve Order
    -> Retrieve Payment
    -> Verify Stock Reduction
    -> Verify Cart Cleanup
    """

    client = TestClient(app)

    # Register

    email = _unique_email("customer")
    password = "Password123!"

    register = client.post(
        "/users",
        json={
            "first_name": "Workflow",
            "last_name": "User",
            "email": email,
            "password": password,
        },
    )

    assert register.status_code == 201

    # Login

    login = client.post(
        "/auth/token",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login.status_code == 200

    access_token = login.json()["access_token"]

    customer_headers = {"Authorization": f"Bearer {access_token}"}

    # Product creation

    product_response = client.post(
        "/products",
        json={
            "name": "Workflow Product",
            "description": "Workflow Test",
            "price": "10.00",
            "stock_quantity": 5,
        },
        headers=_admin_headers(),
    )

    assert product_response.status_code == 201

    product = product_response.json()

    # Add to cart

    add_to_cart = client.post(
        "/cart/items",
        json={
            "product_id": product["id"],
            "quantity": 2,
        },
        headers=customer_headers,
    )

    assert add_to_cart.status_code == 201

    # Cart contains item

    cart_response = client.get(
        "/cart",
        headers=customer_headers,
    )

    assert cart_response.status_code == 200

    cart = cart_response.json()

    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == product["id"]

    # Checkout

    checkout = client.post(
        "/orders/checkout",
        headers={
            **customer_headers,
            "Idempotency-Key": f"workflow-{uuid4().hex}",
        },
        json={"payment_method_id": "pm_test_123"},
    )

    assert checkout.status_code == 201

    order = checkout.json()

    # Order exists

    order_response = client.get(
        f"/orders/{order['id']}",
        headers=customer_headers,
    )

    assert order_response.status_code == 200

    # Payment exists

    payment_id = order.get("payment_id")

    if payment_id:
        payment_response = client.get(
            f"/payments/{payment_id}",
            headers=customer_headers,
        )

        assert payment_response.status_code == 200

        payment = payment_response.json()

        assert payment["status"] == "approved"

    # Stock reduced

    product_after = client.get(f"/products/{product['id']}")

    assert product_after.status_code == 200
    assert product_after.json()["stock_quantity"] == 3

    # Cart removed after checkout

    cart_after = client.get(
        "/cart",
        headers=customer_headers,
    )

    assert cart_after.status_code == 404
