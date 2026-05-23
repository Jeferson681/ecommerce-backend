from types import SimpleNamespace

import pytest

from backend.app.modules.cart import use_cases


class BadItemRepo:
    def __init__(self, session=None):
        self.session = session

    def add_or_increment(self, cart_id: int, product_id: int, quantity: int):
        raise RuntimeError("db down")


class FakeCartRepo:
    def __init__(self, session):
        self.session = session

    def get_or_create_by_user(self, user_id: int):
        return SimpleNamespace(id=1, user_id=user_id)


class UoW:
    def __init__(self):
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_add_item_rolls_back_on_unexpected_exception(monkeypatch):
    monkeypatch.setattr(use_cases, "CartRepository", lambda s: FakeCartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: BadItemRepo(s))

    uow = UoW()

    from backend.app.modules.cart.schemas import CartItemCreate

    with pytest.raises(RuntimeError):
        use_cases.add_item(CartItemCreate(product_id=1, quantity=1), user_id=1, uow=uow)

    assert uow.rolled_back is True
