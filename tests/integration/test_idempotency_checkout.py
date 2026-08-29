from __future__ import annotations

import threading
from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.api.routers.order import get_current_user_id
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.modules.cart.domain.models import Cart, CartItem
from backend.app.modules.order.repositories.order_repository import OrderRepository
from backend.app.modules.product.domain.models import Product
from backend.app.modules.user.domain.models import User

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_concurrent_checkout_only_creates_single_order() -> None:
    session = SessionLocal()

    # prepare product and cart for user 42
    product = Product(
        name="P-conc", description="d", price=Decimal("9.99"), stock_quantity=10
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    user = User(
        id=42,
        first_name="Conc",
        last_name="User",
        email="conc-user-42@example.com",
        password_hash="x",
    )
    session.add(user)
    session.commit()

    cart = Cart(user_id=42)
    session.add(cart)
    session.commit()
    session.refresh(cart)

    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    session.add(item)
    session.commit()
    session.close()

    # make requests act as user 42 (no uow override; let DI create sessions per request)
    app.dependency_overrides[get_current_user_id] = lambda: 42

    idempotency_key = "concurrent-key-1"

    responses: list = []

    def do_request():
        resp = client.post(
            "/orders/checkout",
            json={"payment_method_id": "pm_card_visa"},
            headers={"Idempotency-Key": idempotency_key},
        )
        responses.append(resp)

    t1 = threading.Thread(target=do_request)
    t2 = threading.Thread(target=do_request)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(responses) == 2
    successful_responses = [r for r in responses if r.status_code == 201]
    assert successful_responses

    successful_ids = {response.json()["id"] for response in successful_responses}
    assert len(successful_ids) == 1

    # Current behavior: the reservation becomes visible immediately, so only one
    # checkout succeeds for a shared idempotency key.
    session2 = SessionLocal()
    order_repo = OrderRepository(session2)
    orders = order_repo.list_by_user(42)
    assert len(orders) == 1
    session2.close()
