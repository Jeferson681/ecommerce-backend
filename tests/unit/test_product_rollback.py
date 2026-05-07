import pytest

from app.modules.product import use_cases
from app.modules.product.schemas import ProductCreate, ProductUpdate


class FailingRepo:
    def __init__(self, session):
        pass

    def create(self, product):
        raise RuntimeError("db error")

    def get_by_id(self, pk):
        # used by update/delete tests
        return None

    def update(self, product):
        raise RuntimeError("db error")

    def delete(self, product):
        raise RuntimeError("db error")


class DummyUoW:
    def __init__(self):
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_create_rolls_back_and_propagates(monkeypatch):
    # make Product constructor simple
    class DummyProduct:
        def __init__(self, name, description, price, stock_quantity):
            self.name = name

    monkeypatch.setattr(use_cases, "Product", DummyProduct)
    monkeypatch.setattr(use_cases, "ProductRepository", FailingRepo)

    uow = DummyUoW()
    data = ProductCreate(name="x", description="d", price=1.0, stock_quantity=1)

    with pytest.raises(RuntimeError):
        use_cases.create_product(data, uow)

    assert uow.rolled_back is True


def test_update_rolls_back_on_exception(monkeypatch):
    # prepare repo that returns an object for get_by_id then fails on update
    class Repo:
        def __init__(self, session):
            pass

        def get_by_id(self, pk):
            return type("P", (), {"id": pk, "name": "old"})()

        def update(self, product):
            raise RuntimeError("update fail")

    monkeypatch.setattr(use_cases, "ProductRepository", Repo)

    uow = DummyUoW()
    update = ProductUpdate(name="n")

    with pytest.raises(RuntimeError):
        use_cases.update_product(1, update, uow)

    assert uow.rolled_back is True


def test_delete_rolls_back_on_exception(monkeypatch):
    class Repo:
        def __init__(self, session):
            pass

        def get_by_id(self, pk):
            return type("P", (), {"id": pk})()

        def delete(self, product):
            raise RuntimeError("delete fail")

    monkeypatch.setattr(use_cases, "ProductRepository", Repo)

    uow = DummyUoW()

    with pytest.raises(RuntimeError):
        use_cases.delete_product(1, uow)

    assert uow.rolled_back is True
