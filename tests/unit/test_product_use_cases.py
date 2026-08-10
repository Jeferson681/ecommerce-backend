from datetime import UTC
from types import SimpleNamespace

from backend.app.modules.product import services
from backend.app.modules.product.domain.models import Product
from backend.app.modules.product.schemas import ProductCreate, ProductUpdate


class DummyRepo:
    def __init__(self, session):
        self.session = session
        self.created = False
        self.updated = False

    def create(self, product: Product):
        # simulate DB behavior: set id and timestamps/flags so ProductRead validation succeeds
        self.created = True
        try:
            product.id = 1
        except Exception:
            pass
        product.is_active = getattr(product, "is_active", True)
        from datetime import datetime

        now = datetime.now(UTC)
        product.created_at = getattr(product, "created_at", now)
        product.updated_at = getattr(product, "updated_at", now)

    def get_by_id(self, product_id: int):
        # return a product-like object for update tests
        from datetime import datetime

        now = datetime.now(UTC)

        return SimpleNamespace(
            id=product_id,
            name="old",
            description="old",
            category="old-category",
            image_url=None,
            price=1.0,
            stock_quantity=1,
            is_active=True,
            created_at=now,
            updated_at=now,
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

    monkeypatch.setattr(services, "ProductRepository", fake_repo_factory)

    uow = DummyUoW()
    data = ProductCreate(name="p", description="d", price=1.0, stock_quantity=5)

    # monkeypatch Product class used in use_cases to accept stock_quantity
    class DummyProduct:
        def __init__(
            self, name, description, category, image_url, price, stock_quantity
        ):
            self.name = name
            self.description = description
            self.category = category
            self.image_url = image_url
            self.price = price
            self.stock_quantity = stock_quantity

    monkeypatch.setattr(services, "Product", DummyProduct)

    product = services.create_product(data, uow)

    assert created["repo"].created is True
    assert uow.committed is True
    assert product is not None


def test_update_product_commits_and_updates_fields(monkeypatch):
    # prepare dummy repo that returns a product
    repo = DummyRepo(None)

    def fake_repo_factory(session):
        return repo

    monkeypatch.setattr(services, "ProductRepository", fake_repo_factory)

    uow = DummyUoW()
    update = ProductUpdate(
        name="new", description="new", price=2.5, stock_quantity=10, is_active=False
    )

    product = services.update_product(1, update, uow)

    # repository.update may be removed because the object is attached to the session
    # so we assert commit happened and the returned product has updated fields.
    assert uow.committed is True
    assert product is not None
    assert product.name == "new"
    assert product.description == "new"
    assert product.price == 2.5
    assert product.stock_quantity == 10
    assert product.is_active is False
