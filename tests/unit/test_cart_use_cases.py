# ruff: noqa: B017

"""Comprehensive tests for Cart use cases — happy path, sad path, rollback, and validation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.modules.cart import use_cases
from backend.app.modules.cart.schemas import CartItemCreate, CartItemUpdate

from .conftest import DummyUoW, make_cart, make_cart_item

# ======================================================================
# HAPPY PATH
# ======================================================================


def test_get_cart_existing(monkeypatch) -> None:
    """Getting an existing cart returns a CartRead."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(user_id=user_id)

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: Repo(s))

    result = use_cases.get_cart(user_id=1, uow=DummyUoW())

    assert result.id == 1
    assert result.user_id == 1


def test_add_item_creates_new_cart_and_item(monkeypatch) -> None:
    """Adding an item to a new cart creates the cart and the item."""
    cart_created: list = []
    item_created: list = []

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> None:
            return None

        def create(self, cart: object) -> object:
            cart.id = 1  # type: ignore[attr-defined]
            cart_created.append(cart)
            return cart

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session
            self.created = False

        def get_by_cart_and_product(self, cart_id: int, product_id: int) -> None:
            return None

        def create(self, cart_item: object) -> object:
            self.created = True
            now = datetime.now(UTC)
            item_created.append(cart_item)
            from types import SimpleNamespace

            return SimpleNamespace(
                id=1,
                cart_id=cart_item.cart_id,  # type: ignore[attr-defined]
                product_id=cart_item.product_id,  # type: ignore[attr-defined]
                quantity=cart_item.quantity,  # type: ignore[attr-defined]
                created_at=now,
                updated_at=now,
            )

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: ItemRepo(s))

    from types import SimpleNamespace

    monkeypatch.setattr(use_cases, "Cart", lambda **kw: SimpleNamespace(**kw))

    uow = DummyUoW()
    data = CartItemCreate(product_id=5, quantity=2)
    item = use_cases.add_item(data, user_id=1, uow=uow)

    assert uow.committed is True
    assert item.product_id == 5
    assert item.quantity == 2
    assert len(cart_created) == 1
    assert len(item_created) == 1


def test_add_item_updates_existing_quantity(monkeypatch) -> None:
    """Adding an item that already exists increments the quantity."""
    updated: list = []

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

        def create(self, cart: object) -> object:
            cart.id = 1  # type: ignore[attr-defined]
            return cart

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_cart_and_product(self, cart_id: int, product_id: int) -> object:
            return make_cart_item(
                id=2, cart_id=cart_id, product_id=product_id, quantity=1
            )

        def create(self, cart_item: object) -> object:
            return cart_item

        def update(self, cart_item: object) -> object:
            updated.append(cart_item)
            return cart_item

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: ItemRepo(s))

    uow = DummyUoW()
    data = CartItemCreate(product_id=7, quantity=3)
    item = use_cases.add_item(data, user_id=2, uow=uow)

    assert uow.committed is True
    assert item.quantity == 4  # original 1 + new 3
    assert len(updated) == 1


def test_update_item_commits_and_updates(monkeypatch) -> None:
    """Updating an existing cart item commits and returns updated item."""
    updated: list = []

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, item_id: int) -> object:
            return make_cart_item(id=item_id, cart_id=1)

        def update(self, cart_item: object) -> object:
            updated.append(cart_item)
            return cart_item

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: ItemRepo(s))

    uow = DummyUoW()
    result = use_cases.update_item(1, CartItemUpdate(quantity=5), user_id=10, uow=uow)

    assert uow.committed is True
    assert result.quantity == 5
    assert len(updated) == 1


def test_remove_item_commits_and_deletes(monkeypatch) -> None:
    """Removing an existing cart item commits and returns None."""
    deleted: list = []

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, item_id: int) -> object:
            return make_cart_item(id=item_id, cart_id=1)

        def delete(self, cart_item: object) -> None:
            deleted.append(cart_item)

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: ItemRepo(s))

    uow = DummyUoW()
    use_cases.remove_item(1, user_id=20, uow=uow)

    assert uow.committed is True
    assert len(deleted) == 1


# ======================================================================
# SAD PATH – not found / validation errors
# ======================================================================


def test_get_cart_raises_not_found_when_missing(monkeypatch) -> None:
    """Getting a non-existent cart raises NotFoundError."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="Cart not found"):
        use_cases.get_cart(user_id=10, uow=DummyUoW())


def test_update_item_raises_not_found_when_cart_missing(monkeypatch) -> None:
    """Updating an item when cart is missing raises NotFoundError."""

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))

    with pytest.raises(NotFoundError, match="Cart not found"):
        use_cases.update_item(1, CartItemUpdate(quantity=1), user_id=99, uow=DummyUoW())


def test_update_item_raises_not_found_when_item_missing(monkeypatch) -> None:
    """Updating a non-existent item raises NotFoundError."""

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, item_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: ItemRepo(s))

    with pytest.raises(NotFoundError, match="Cart item not found"):
        use_cases.update_item(
            999, CartItemUpdate(quantity=3), user_id=1, uow=DummyUoW()
        )


def test_update_item_raises_not_found_when_item_belongs_to_another_cart(
    monkeypatch,
) -> None:
    """Updating an item that belongs to a different cart raises NotFoundError."""

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, item_id: int) -> object:
            return make_cart_item(id=item_id, cart_id=999)  # different cart

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: ItemRepo(s))

    with pytest.raises(NotFoundError, match="Cart item not found"):
        use_cases.update_item(1, CartItemUpdate(quantity=3), user_id=1, uow=DummyUoW())


def test_remove_item_raises_not_found_when_cart_missing(monkeypatch) -> None:
    """Removing an item when cart is missing raises NotFoundError."""

    class Repo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: Repo(s))

    with pytest.raises(NotFoundError, match="Cart not found"):
        use_cases.remove_item(1, user_id=5, uow=DummyUoW())


def test_remove_item_raises_not_found_when_item_missing(monkeypatch) -> None:
    """Removing a non-existent item raises NotFoundError."""

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, item_id: int) -> None:
            return None

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: ItemRepo(s))

    with pytest.raises(NotFoundError, match="Cart item not found"):
        use_cases.remove_item(999, user_id=1, uow=DummyUoW())


# ======================================================================
# ROLLBACK TESTS
# ======================================================================


def test_add_item_rolls_back_on_unexpected_exception(monkeypatch) -> None:
    """If an unexpected error occurs during add_item, the UoW rolls back."""

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

    class BadItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_cart_and_product(self, cart_id: int, product_id: int) -> object:
            raise RuntimeError("db down")

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: BadItemRepo(s))

    uow = DummyUoW()
    data = CartItemCreate(product_id=1, quantity=1)

    with pytest.raises(RuntimeError, match="db down"):
        use_cases.add_item(data, user_id=1, uow=uow)

    assert uow.rolled_back is True


def test_update_item_rolls_back_on_commit_error(monkeypatch) -> None:
    """If commit fails during update_item, the UoW rolls back."""

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, item_id: int) -> object:
            return make_cart_item(id=item_id, cart_id=1)

        def update(self, cart_item: object) -> object:
            return cart_item

    class FailingUoW(DummyUoW):
        def commit(self) -> None:
            raise RuntimeError("commit fail")

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: ItemRepo(s))

    with pytest.raises(RuntimeError, match="commit fail"):
        use_cases.update_item(
            1, CartItemUpdate(quantity=5), user_id=1, uow=FailingUoW()
        )


def test_remove_item_rolls_back_on_unexpected_exception(monkeypatch) -> None:
    """If an unexpected error occurs during remove_item, the UoW rolls back."""

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> object:
            return make_cart(id=1, user_id=user_id)

    class BadItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, item_id: int) -> object:
            return make_cart_item(id=item_id, cart_id=1)

        def delete(self, cart_item: object) -> None:
            raise RuntimeError("delete fail")

    monkeypatch.setattr(use_cases, "CartRepository", lambda s: CartRepo(s))
    monkeypatch.setattr(use_cases, "CartItemRepository", lambda s: BadItemRepo(s))

    uow = DummyUoW()
    with pytest.raises(RuntimeError, match="delete fail"):
        use_cases.remove_item(1, user_id=1, uow=uow)

    assert uow.rolled_back is True


# ======================================================================
# VALIDATION – schema tests
# ======================================================================


class TestCartItemCreateValidation:
    def test_valid_item(self) -> None:
        data = CartItemCreate(product_id=1, quantity=2)
        assert data.product_id == 1
        assert data.quantity == 2

    def test_valid_item_default_quantity(self) -> None:
        data = CartItemCreate(product_id=1)
        assert data.quantity == 1

    def test_invalid_product_id_zero(self) -> None:
        with pytest.raises(Exception):
            CartItemCreate(product_id=0, quantity=1)

    def test_invalid_product_id_negative(self) -> None:
        with pytest.raises(Exception):
            CartItemCreate(product_id=-1, quantity=1)

    def test_invalid_quantity_zero(self) -> None:
        with pytest.raises(Exception):
            CartItemCreate(product_id=1, quantity=0)


class TestCartItemUpdateValidation:
    def test_valid_update(self) -> None:
        data = CartItemUpdate(quantity=3)
        assert data.quantity == 3

    def test_invalid_quantity_zero(self) -> None:
        with pytest.raises(Exception):
            CartItemUpdate(quantity=0)

    def test_invalid_quantity_negative(self) -> None:
        with pytest.raises(Exception):
            CartItemUpdate(quantity=-1)
