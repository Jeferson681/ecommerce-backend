from datetime import UTC
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.core.exceptions import NotFoundError
from backend.app.modules.cart import use_cases
from backend.app.modules.cart.schemas import CartItemCreate, CartItemUpdate


class DummyCartRepo:
    def __init__(self, session=None):
        self.session = session
        self.created = False

    def get_by_user_id(self, user_id: int):
        return None

    def create(self, cart):
        # simulate DB behavior
        self.created = True
        try:
            cart.id = 1
        except Exception:
            pass
        from datetime import datetime

        now = datetime.now(UTC)
        cart.created_at = getattr(cart, "created_at", now)
        cart.updated_at = getattr(cart, "updated_at", now)
        cart.items = getattr(cart, "items", [])
        return cart

    def get_or_create_by_user(self, user_id: int):
        return SimpleNamespace(id=1, user_id=user_id, items=[])


class DummyCartItemRepo:
    def __init__(self, session=None):
        self.session = session
        self.added = False
        self.updated = False
        self.deleted = False

    def add_or_increment(self, cart_id: int, product_id: int, quantity: int):
        self.added = True
        from datetime import datetime

        now = datetime.now(UTC)
        return SimpleNamespace(
            id=1,
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
            created_at=now,
            updated_at=now,
        )

    def get_by_cart_and_product(self, cart_id: int, product_id: int):
        return None

    def get_by_id(self, item_id: int):
        from datetime import datetime

        now = datetime.now(UTC)
        return SimpleNamespace(
            id=item_id,
            cart_id=1,
            product_id=2,
            quantity=1,
            created_at=now,
            updated_at=now,
        )

    def update(self, cart_item):
        self.updated = True
        from datetime import datetime

        cart_item.updated_at = getattr(cart_item, "updated_at", datetime.now(UTC))
        return cart_item

    def delete(self, cart_item):
        self.deleted = True


class DummyUoW:
    def __init__(self):
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_get_cart_creates_when_missing(monkeypatch):
    repo = DummyCartRepo()

    def fake_repo_factory(session):
        return repo

    monkeypatch.setattr(use_cases, "CartRepository", fake_repo_factory)

    uow = DummyUoW()

    # monkeypatch Cart class used in use_cases to a simple DummyCart
    class DummyCart:
        def __init__(self, user_id):
            self.user_id = user_id

    monkeypatch.setattr(use_cases, "Cart", DummyCart)

    # call get_cart and expect a CartRead-like object returned
    cart = use_cases.get_cart(user_id=10, uow=uow)

    assert repo.created is True
    assert uow.committed is True
    assert cart.user_id == 10


def test_add_item_calls_repo_and_commits(monkeypatch):
    created = {}

    def fake_cart_repo(session):
        return DummyCartRepo(session)

    def fake_item_repo(session):
        repo = DummyCartItemRepo(session)
        created["item_repo"] = repo
        return repo

    monkeypatch.setattr(use_cases, "CartRepository", fake_cart_repo)
    monkeypatch.setattr(use_cases, "CartItemRepository", fake_item_repo)

    uow = DummyUoW()
    data = CartItemCreate(product_id=5, quantity=2)

    # ensure Cart class is a simple test-friendly struct
    class DummyCart:
        def __init__(self, user_id):
            self.user_id = user_id

    monkeypatch.setattr(use_cases, "Cart", DummyCart)

    item = use_cases.add_item(data, user_id=1, uow=uow)

    assert created["item_repo"].added is True
    assert uow.committed is True
    assert item.product_id == 5
    assert item.quantity == 2


def test_add_item_handles_integrity_error_and_updates_existing(monkeypatch):
    # simulate first add raising IntegrityError, then existing item found and updated
    class BadAddRepo(DummyCartItemRepo):
        def __init__(self, session=None):
            super().__init__(session)
            self.called = 0

        def add_or_increment(self, cart_id: int, product_id: int, quantity: int):
            self.called += 1
            if self.called == 1:
                raise IntegrityError("msg", params=None, orig=None)
            return super().add_or_increment(cart_id, product_id, quantity)

        def get_by_cart_and_product(self, cart_id: int, product_id: int):
            from datetime import datetime

            now = datetime.now(UTC)
            return SimpleNamespace(
                id=2,
                cart_id=cart_id,
                product_id=product_id,
                quantity=1,
                created_at=now,
                updated_at=now,
            )

    def fake_cart_repo(session):
        return DummyCartRepo(session)

    def fake_item_repo(session):
        return BadAddRepo(session)

    monkeypatch.setattr(use_cases, "CartRepository", fake_cart_repo)
    monkeypatch.setattr(use_cases, "CartItemRepository", fake_item_repo)

    uow = DummyUoW()
    data = CartItemCreate(product_id=7, quantity=3)

    class DummyCart:
        def __init__(self, user_id):
            self.user_id = user_id

    monkeypatch.setattr(use_cases, "Cart", DummyCart)

    item = use_cases.add_item(data, user_id=2, uow=uow)

    assert uow.committed is True
    assert item.product_id == 7


def test_update_item_commits_and_updates_fields(monkeypatch):
    # prepare dummy repos
    item_repo = DummyCartItemRepo()

    class FakeCartRepo:
        def __init__(self, session):
            self.session = session

        def get_by_user_id(self, user_id: int):
            return SimpleNamespace(id=1, user_id=user_id)

    def fake_cart_repo(session):
        return FakeCartRepo(session)

    def fake_item_repo(session):
        return item_repo

    monkeypatch.setattr(use_cases, "CartRepository", fake_cart_repo)
    monkeypatch.setattr(use_cases, "CartItemRepository", fake_item_repo)

    uow = DummyUoW()
    update = CartItemUpdate(quantity=5)

    item = use_cases.update_item(1, update, user_id=10, uow=uow)

    assert uow.committed is True
    assert item.quantity == 5


def test_update_item_raises_if_missing(monkeypatch):
    class Repo:
        def __init__(self, session):
            self.session = session

        def get_by_user_id(self, user_id: int):
            return None

    monkeypatch.setattr(use_cases, "CartRepository", Repo)
    monkeypatch.setattr(
        use_cases, "CartItemRepository", lambda session: DummyCartItemRepo()
    )

    uow = DummyUoW()
    with pytest.raises(NotFoundError):
        use_cases.update_item(1, CartItemUpdate(quantity=1), user_id=99, uow=uow)


def test_remove_item_commits_and_deletes(monkeypatch):
    item_repo = DummyCartItemRepo()

    class FakeCartRepo2:
        def __init__(self, session):
            self.session = session

        def get_by_user_id(self, user_id: int):
            return SimpleNamespace(id=1, user_id=user_id)

    def fake_cart_repo(session):
        return FakeCartRepo2(session)

    def fake_item_repo(session):
        return item_repo

    monkeypatch.setattr(use_cases, "CartRepository", fake_cart_repo)
    monkeypatch.setattr(use_cases, "CartItemRepository", fake_item_repo)

    uow = DummyUoW()

    use_cases.remove_item(1, user_id=20, uow=uow)

    assert item_repo.deleted is True
    assert uow.committed is True
