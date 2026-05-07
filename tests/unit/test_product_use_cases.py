from types import SimpleNamespace

from app.modules.product import use_cases
from app.modules.product.domain.models import Product
from app.modules.product.schemas import ProductCreate, ProductUpdate


class DummyRepo:
    def __init__(self, session):
        self.session = session
        self.created = False
        self.updated = False

    def create(self, product: Product):
        self.created = True

    def get_by_id(self, product_id: int):
        # return a product-like object for update tests
        return SimpleNamespace(
            id=product_id,
            name="old",
            description="old",
            price=1.0,
            stock_quantity=1,
            is_active=True,
        )

    def update(self, product: Product):
        self.updated = True


class DummyUoW:
    def __init__(self):
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_create_product_calls_repo_and_commit(monkeypatch):
    created = {}

    def fake_repo_factory(session):
        repo = DummyRepo(session)
        created["repo"] = repo
        return repo

    monkeypatch.setattr(use_cases, "ProductRepository", fake_repo_factory)

    uow = DummyUoW()
    data = ProductCreate(name="p", description="d", price=1.0, stock_quantity=5)

    # monkeypatch Product class used in use_cases to accept stock_quantity
    class DummyProduct:
        def __init__(self, name, description, price, stock_quantity):
            self.name = name
            self.description = description
            self.price = price
            self.stock_quantity = stock_quantity

    monkeypatch.setattr(use_cases, "Product", DummyProduct)

    product = use_cases.create_product(data, uow)

    assert created["repo"].created is True
    assert uow.committed is True
    assert product is not None


def test_update_product_commits_and_updates_fields(monkeypatch):
    # prepare dummy repo that returns a product
    repo = DummyRepo(None)

    def fake_repo_factory(session):
        return repo

    monkeypatch.setattr(use_cases, "ProductRepository", fake_repo_factory)

    uow = DummyUoW()
    update = ProductUpdate(
        name="new", description="new", price=2.5, stock_quantity=10, is_active=False
    )

    product = use_cases.update_product(1, update, uow)

    assert repo.updated is True
    assert uow.committed is True
    assert product is not None
