from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from backend.app.modules.order import use_cases
from backend.app.modules.order.schemas import OrderRead


class DummyCartRepo:
    def __init__(self, session=None):
        self.session = session

    def get_by_user_id(self, user_id: int):
        return SimpleNamespace(id=1, user_id=user_id)

    def delete(self, cart):
        # simulate deletion
        return None


class DummyCartItemRepo:
    def __init__(self, session=None):
        self.session = session

    def get_by_cart_id(self, cart_id: int):
        return [
            SimpleNamespace(id=1, cart_id=cart_id, product_id=2, quantity=2),
        ]


class DummyProductRepo:
    def __init__(self, session=None):
        self.session = session

    def get_by_id(self, product_id: int):
        return SimpleNamespace(id=product_id, price=Decimal("10.00"), stock_quantity=10)


class DummyOrderRepo:
    def __init__(self, session=None):
        self.session = session

    def create(self, order):
        order.id = 1
        return order

    def get_by_id(self, order_id: int):
        from datetime import datetime

        now = datetime.now()
        return SimpleNamespace(
            id=order_id, user_id=1, items=[], created_at=now, updated_at=now
        )


class DummyOrderItemRepo:
    def __init__(self, session=None):
        self.session = session

    def create(self, item):
        item.id = 1
        return item


class DummyProductRepoUpdated(DummyProductRepo):
    def update(self, product):
        return product

    def decrement_stock_if_enough(self, product_id: int, quantity: int) -> bool:
        # For tests, simulate successful atomic decrement when called.
        return True


class DummyUoW:
    def __init__(self):
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def flush(self):
        # no-op flush for compatibility with UoW implementation
        return None


def test_checkout_happy_path(monkeypatch):
    monkeypatch.setattr(use_cases, "CartRepository", lambda s: DummyCartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: DummyCartItemRepo(s))
    monkeypatch.setattr(
        use_cases, "ProductRepository", lambda s: DummyProductRepoUpdated(s)
    )
    monkeypatch.setattr(use_cases, "OrderRepository", lambda s: DummyOrderRepo(s))
    monkeypatch.setattr(
        use_cases, "OrderItemRepository", lambda s: DummyOrderItemRepo(s)
    )

    uow = DummyUoW()

    order = use_cases.checkout(user_id=1, uow=uow)

    assert uow.committed is True
    assert isinstance(order, OrderRead)
