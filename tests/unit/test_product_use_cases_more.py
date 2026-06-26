from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.modules.product import services
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


def test_get_product_raises_not_found_when_missing(monkeypatch):
    """get_product now raises NotFoundError instead of returning None."""
    repo = DummyRepo2()

    def fake_repo_factory(session):
        return repo

    monkeypatch.setattr(services, "ProductRepository", fake_repo_factory)

    uow = DummyUoW2()

    with pytest.raises(NotFoundError, match="Product not found"):
        services.get_product(1, uow)


def test_list_products_returns_empty(monkeypatch):
    class Repo:
        def __init__(self, session):
            pass

        def list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(services, "ProductRepository", Repo)

    uow = DummyUoW2()
    result = services.list_products(uow)
    assert result == []


def test_update_product_raises_if_missing(monkeypatch):
    class Repo:
        def __init__(self, session):
            pass

        def get_by_id(self, _):
            return None

    monkeypatch.setattr(services, "ProductRepository", Repo)

    uow = DummyUoW2()
    update = ProductUpdate(name="a")

    with pytest.raises(NotFoundError):
        services.update_product(1, update, uow)


def test_delete_product_commits_and_calls_delete(monkeypatch):
    repo = DummyRepo2()

    def fake_repo_factory(session):
        return repo

    monkeypatch.setattr(services, "ProductRepository", fake_repo_factory)

    uow = DummyUoW2()

    # monkeypatch get_by_id to return a simple object
    repo.get_by_id = lambda pk: SimpleNamespace(id=pk)  # type: ignore[assignment]

    result = services.delete_product(1, uow)

    # delete_product intentionally returns None on success
    assert result is None
    assert uow.committed is True
