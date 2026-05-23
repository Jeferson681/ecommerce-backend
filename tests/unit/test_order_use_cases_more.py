from __future__ import annotations

import pytest

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.modules.order import use_cases


def test_checkout_raises_when_cart_missing(monkeypatch):
    class Repo:
        def __init__(self, session):
            self.session = session

        def get_by_user_id(self, user_id: int):
            return None

    monkeypatch.setattr(use_cases, "CartRepository", Repo)

    class DummyUoW:
        def __init__(self):
            self.session = object()

        def commit(self):
            # noop for tests
            pass

        def rollback(self):
            # noop for tests
            pass

    uow = DummyUoW()

    with pytest.raises(NotFoundError):
        use_cases.checkout(user_id=999, uow=uow)


def test_checkout_raises_on_empty_cart(monkeypatch):
    # simulate cart exists but items empty via cart_item repo
    from types import SimpleNamespace

    class CartRepo2:
        def __init__(self, session):
            self.session = session

        def get_by_user_id(self, user_id: int):
            return SimpleNamespace(id=1, user_id=user_id)

    class EmptyItemRepo:
        def __init__(self, session):
            self.session = session

        def get_by_cart_id(self, cart_id: int):
            return []

    monkeypatch.setattr(use_cases, "CartRepository", CartRepo2)
    monkeypatch.setattr(use_cases, "CartItemRepository", EmptyItemRepo)

    class DummyUoW:
        def __init__(self):
            self.session = object()

        def commit(self):
            # noop for tests
            pass

        def rollback(self):
            # noop for tests
            pass

    uow = DummyUoW()

    with pytest.raises(ValidationError):
        use_cases.checkout(user_id=1, uow=uow)
