from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.modules.order import use_cases


def test_checkout_rolls_back_on_integrity_error(monkeypatch):
    from decimal import Decimal
    from types import SimpleNamespace

    class CartRepo:
        def __init__(self, session):
            self.session = session

        def get_by_user_id(self, user_id: int):
            return SimpleNamespace(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session):
            self.session = session

        def get_by_cart_id(self, cart_id: int):
            return [SimpleNamespace(product_id=1, quantity=1)]

    class ProductRepo:
        def __init__(self, session):
            self.session = session

        def get_by_id(self, product_id: int):
            return SimpleNamespace(
                id=product_id, price=Decimal("10.00"), stock_quantity=10
            )

    class BadOrderItemRepo:
        def __init__(self, session):
            self.session = session

        def create(self, item):
            # raise IntegrityError with a real exception as `orig` to satisfy type checks
            raise IntegrityError("msg", {}, Exception("orig"))

    class UoW:
        def __init__(self):
            # provide a session attribute for repository constructors
            self.session = object()
            self.committed = False
            self.rolled_back = False

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

    monkeypatch.setattr(use_cases, "CartRepository", CartRepo)
    monkeypatch.setattr(use_cases, "CartItemRepository", ItemRepo)
    monkeypatch.setattr(use_cases, "ProductRepository", ProductRepo)
    monkeypatch.setattr(
        use_cases,
        "OrderRepository",
        lambda s: SimpleNamespace(create=lambda order: SimpleNamespace(id=1)),
    )
    monkeypatch.setattr(use_cases, "OrderItemRepository", lambda s: BadOrderItemRepo(s))

    uow = UoW()

    with pytest.raises(IntegrityError):
        use_cases.checkout(user_id=1, uow=uow)

    assert uow.rolled_back is True
