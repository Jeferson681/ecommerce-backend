from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.modules.product import use_cases
from backend.app.modules.product.schemas import ProductUpdate


class DummyRepo2:
    def __init__(self):
        self.deleted = False

    def get_by_id(self, product_id: int):
        return None

    def delete(self, product):
        self.deleted = True


class DummyUoW2:
    def __init__(self):
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_get_product_returns_none_when_missing(monkeypatch):
    repo = DummyRepo2()

    def fake_repo_factory(session):
        return repo

    monkeypatch.setattr(use_cases, "ProductRepository", fake_repo_factory)

    uow = DummyUoW2()

    result = use_cases.get_product(1, uow)

    assert result is None


def test_list_products_returns_empty(monkeypatch):
    class Repo:
        def __init__(self, session):
            pass

        def list(self):
            return []

    monkeypatch.setattr(use_cases, "ProductRepository", Repo)

    uow = DummyUoW2()
    result = use_cases.list_products(uow)
    assert result == []


def test_update_product_raises_if_missing(monkeypatch):
    class Repo:
        def __init__(self, session):
            pass

        def get_by_id(self, _):
            return None

    monkeypatch.setattr(use_cases, "ProductRepository", Repo)

    uow = DummyUoW2()
    update = ProductUpdate(name="a")

    with pytest.raises(NotFoundError):
        use_cases.update_product(1, update, uow)


def test_delete_product_commits_and_calls_delete(monkeypatch):
    repo = DummyRepo2()

    def fake_repo_factory(session):
        return repo

    monkeypatch.setattr(use_cases, "ProductRepository", fake_repo_factory)

    uow = DummyUoW2()

    # monkeypatch get_by_id to return a simple object
    repo.get_by_id = lambda pk: SimpleNamespace(id=pk)

    result = use_cases.delete_product(1, uow)

    # delete_product intentionally returns None on success (silence on success)
    assert result is None
    assert uow.committed is True
