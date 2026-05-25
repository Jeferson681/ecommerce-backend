# ruff: noqa: B017

"""Comprehensive tests for Order use cases — happy path, sad path, rollback, and validation."""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import (
    NotFoundError as CoreNotFoundError,
    ValidationError as CoreValidationError,
)
from backend.app.modules.order import use_cases
from backend.app.modules.order.schemas import OrderItemRead, OrderRead

from .conftest import DummyUoW, make_cart, make_cart_item, make_order, make_product


def _stub_payment_use_case(monkeypatch) -> None:
    monkeypatch.setattr(
        use_cases, "process_payment_use_case", lambda *args, **kwargs: None
    )


# ======================================================================
# HAPPY PATH
# ======================================================================


class TestCheckoutHappyPath:
    """Successful checkout flows."""

    def _setup_repos(self, monkeypatch) -> tuple[DummyUoW, SimpleNamespace]:
        """Set up all dummy repositories for a successful checkout."""
        uow = DummyUoW()

        class CartRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> SimpleNamespace:
                return make_cart(id=1, user_id=user_id)

            def delete(self, cart: object) -> None:
                pass

        class CartItemRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_cart_id(self, cart_id: int) -> list[SimpleNamespace]:
                return [
                    make_cart_item(id=1, cart_id=cart_id, product_id=2, quantity=2),
                ]

        class ProductRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, product_id: int) -> SimpleNamespace:
                return make_product(
                    id=product_id, price=Decimal("10.00"), stock_quantity=10
                )

            def decrement_stock_if_enough(self, product_id: int, quantity: int) -> bool:
                return True

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def create(self, order: object) -> object:
                order.id = 1  # type: ignore[attr-defined]
                return order

            def get_by_id(self, order_id: int) -> SimpleNamespace:
                return make_order(id=order_id, user_id=1, items=[])

        class OrderItemRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def create(self, item: object) -> object:
                item.id = 1  # type: ignore[attr-defined]
                return item

        class IdempotencyRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_key(self, key: str, user_id: int | None = None) -> None:
                return None

            def save(self, record: object) -> None:
                pass

        monkeypatch.setattr(use_cases, "CartRepository", CartRepo)
        monkeypatch.setattr(use_cases, "CartItemRepository", CartItemRepo)
        monkeypatch.setattr(use_cases, "ProductRepository", ProductRepo)
        monkeypatch.setattr(use_cases, "OrderRepository", OrderRepo)
        monkeypatch.setattr(use_cases, "OrderItemRepository", OrderItemRepo)
        monkeypatch.setattr(use_cases, "IdempotencyRepository", IdempotencyRepo)
        _stub_payment_use_case(monkeypatch)

        return uow, SimpleNamespace()

    def test_checkout_creates_order_without_idempotency(self, monkeypatch) -> None:
        """Checkout without idempotency key creates order and commits."""
        uow, _ = self._setup_repos(monkeypatch)
        order = use_cases.checkout(user_id=1, uow=uow)

        assert uow.committed is True
        assert isinstance(order, OrderRead)

    def test_checkout_with_idempotency_key(self, monkeypatch) -> None:
        """Checkout with idempotency key creates order once."""
        uow = DummyUoW()

        class CartRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> SimpleNamespace:
                return make_cart(id=1, user_id=user_id)

            def delete(self, cart: object) -> None:
                pass

        class CartItemRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_cart_id(self, cart_id: int) -> list[SimpleNamespace]:
                return [make_cart_item(id=1, cart_id=cart_id, product_id=2, quantity=2)]

        class ProductRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, product_id: int) -> SimpleNamespace:
                return make_product(
                    id=product_id, price=Decimal("10.00"), stock_quantity=10
                )

            def decrement_stock_if_enough(self, product_id: int, quantity: int) -> bool:
                return True

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def create(self, order: object) -> object:
                order.id = 1  # type: ignore[attr-defined]
                return order

            def get_by_id(self, order_id: int) -> SimpleNamespace:
                return make_order(id=order_id, user_id=1, items=[])

        class OrderItemRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def create(self, item: object) -> object:
                item.id = 1  # type: ignore[attr-defined]
                return item

        class IdempotencyRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_key(self, key: str, user_id: int | None = None) -> None:
                return None

            def claim(self, record: object) -> tuple[object, bool]:
                return (record, True)

            def save_response(
                self, key: str, user_id: int, status: int, body: str
            ) -> None:
                pass

        monkeypatch.setattr(use_cases, "CartRepository", CartRepo)
        monkeypatch.setattr(use_cases, "CartItemRepository", CartItemRepo)
        monkeypatch.setattr(use_cases, "ProductRepository", ProductRepo)
        monkeypatch.setattr(use_cases, "OrderRepository", OrderRepo)
        monkeypatch.setattr(use_cases, "OrderItemRepository", OrderItemRepo)
        monkeypatch.setattr(use_cases, "IdempotencyRepository", IdempotencyRepo)
        _stub_payment_use_case(monkeypatch)

        order = use_cases.checkout(
            user_id=1, uow=uow, idempotency_key="key-123", request_hash="hash-abc"
        )

        assert uow.committed is True
        assert isinstance(order, OrderRead)


class TestGetOrderHappyPath:
    def test_owner_can_get_order(self, monkeypatch) -> None:
        """Order owner can retrieve their own order."""

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, order_id: int) -> SimpleNamespace:
                return make_order(id=order_id, user_id=1)

        monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))

        order = use_cases.get_order(order_id=1, user_id=1, uow=DummyUoW())
        assert order.id == 1
        assert order.user_id == 1

    def test_admin_can_get_any_order(self, monkeypatch) -> None:
        """Admin can retrieve any user's order."""

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, order_id: int) -> SimpleNamespace:
                return make_order(id=order_id, user_id=2)  # not the requestor

        class UserRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, user_id: int) -> SimpleNamespace:
                from datetime import UTC, datetime

                return SimpleNamespace(
                    id=user_id,
                    first_name="Admin",
                    last_name="User",
                    email="admin@mail.com",
                    role="admin",
                    is_active=True,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )

        monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))
        monkeypatch.setattr(use_cases, "UserRepository", lambda s: UserRepo(s))

        order = use_cases.get_order(
            order_id=1, user_id=2, uow=DummyUoW(), requesting_user_id=999
        )
        assert order.id == 1

    def test_list_orders_returns_user_orders(self, monkeypatch) -> None:
        """Listing orders returns all orders for the authenticated user."""

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> list[SimpleNamespace]:
                return [
                    make_order(id=1, user_id=user_id),
                    make_order(id=2, user_id=user_id),
                ]

        monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))

        orders = use_cases.list_orders(user_id=1, uow=DummyUoW())
        assert len(orders) == 2
        assert orders[0].id == 1
        assert orders[1].id == 2


# ======================================================================
# SAD PATH – not found / validation errors
# ======================================================================


class TestCheckoutSadPath:
    def test_checkout_raises_when_cart_missing(self, monkeypatch) -> None:
        """Checkout with a non-existent cart raises NotFoundError."""

        class CartRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> None:
                return None

        monkeypatch.setattr(use_cases, "CartRepository", CartRepo)

        with pytest.raises(CoreNotFoundError, match="Cart not found"):
            use_cases.checkout(user_id=999, uow=DummyUoW())

    def test_checkout_raises_on_empty_cart(self, monkeypatch) -> None:
        """Checkout with an empty cart raises ValidationError."""

        class CartRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> SimpleNamespace:
                return make_cart(id=1, user_id=user_id)

        class EmptyItemRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_cart_id(self, cart_id: int) -> list:
                return []

        monkeypatch.setattr(use_cases, "CartRepository", CartRepo)
        monkeypatch.setattr(use_cases, "CartItemRepository", EmptyItemRepo)
        _stub_payment_use_case(monkeypatch)

        with pytest.raises(CoreValidationError, match="Cart is empty"):
            use_cases.checkout(user_id=1, uow=DummyUoW())

    def test_checkout_raises_when_product_not_found(self, monkeypatch) -> None:
        """Checkout with a missing product raises NotFoundError."""

        class CartRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> SimpleNamespace:
                return make_cart(id=1, user_id=user_id)

        class CartItemRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_cart_id(self, cart_id: int) -> list[SimpleNamespace]:
                return [make_cart_item(id=1, cart_id=cart_id, product_id=999)]

        class ProductRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, product_id: int) -> None:
                return None  # product not found

        monkeypatch.setattr(use_cases, "CartRepository", CartRepo)
        monkeypatch.setattr(use_cases, "CartItemRepository", CartItemRepo)
        monkeypatch.setattr(use_cases, "ProductRepository", ProductRepo)
        _stub_payment_use_case(monkeypatch)

        with pytest.raises(CoreNotFoundError, match="Product not found"):
            use_cases.checkout(user_id=1, uow=DummyUoW())

    def test_checkout_raises_on_insufficient_stock(self, monkeypatch) -> None:
        """Checkout with insufficient stock raises ValidationError."""

        class CartRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> SimpleNamespace:
                return make_cart(id=1, user_id=user_id)

        class CartItemRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_cart_id(self, cart_id: int) -> list[SimpleNamespace]:
                return [
                    make_cart_item(id=1, cart_id=cart_id, product_id=2, quantity=20)
                ]

        class ProductRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, product_id: int) -> SimpleNamespace:
                return make_product(id=product_id, stock_quantity=5)  # insufficient

        monkeypatch.setattr(use_cases, "CartRepository", CartRepo)
        monkeypatch.setattr(use_cases, "CartItemRepository", CartItemRepo)
        monkeypatch.setattr(use_cases, "ProductRepository", ProductRepo)
        _stub_payment_use_case(monkeypatch)

        with pytest.raises(CoreValidationError, match="Insufficient stock"):
            use_cases.checkout(user_id=1, uow=DummyUoW())

    def test_checkout_raises_on_mismatched_idempotency_params(
        self, monkeypatch
    ) -> None:
        """Providing only one of idempotency_key/request_hash raises ValidationError."""
        from backend.app.core.exceptions import ValidationError as CoreValidationError2

        with pytest.raises(
            CoreValidationError2, match="Both idempotency_key and request_hash"
        ):
            use_cases.checkout(user_id=1, uow=DummyUoW(), idempotency_key="only-key")


class TestGetOrderSadPath:
    def test_get_order_raises_not_found_when_missing(self, monkeypatch) -> None:
        """Getting a non-existent order raises NotFoundError."""

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, order_id: int) -> None:
                return None

        monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))

        with pytest.raises(CoreNotFoundError, match="Order not found"):
            use_cases.get_order(order_id=999, user_id=1, uow=DummyUoW())

    def test_get_order_raises_for_non_owner_non_admin(self, monkeypatch) -> None:
        """A non-owner, non-admin user cannot access another user's order."""

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, order_id: int) -> SimpleNamespace:
                return make_order(id=order_id, user_id=2)  # owned by user 2

        class UserRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, user_id: int) -> SimpleNamespace:
                from datetime import UTC, datetime

                return SimpleNamespace(
                    id=user_id,
                    first_name="Regular",
                    last_name="User",
                    email="regular@mail.com",
                    role="user",
                    is_active=True,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )

        monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))
        monkeypatch.setattr(use_cases, "UserRepository", lambda s: UserRepo(s))

        # user_id=3 is not the owner (owner is user_id=2) and requesting_user_id=3 is not admin
        with pytest.raises(CoreNotFoundError, match="Order not found"):
            use_cases.get_order(
                order_id=1, user_id=3, uow=DummyUoW(), requesting_user_id=3
            )

    def test_list_orders_empty(self, monkeypatch) -> None:
        """Listing orders for a user with no orders returns an empty list."""

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> list:
                return []

        monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))

        orders = use_cases.list_orders(user_id=999, uow=DummyUoW())
        assert orders == []


# ======================================================================
# ROLLBACK TESTS
# ======================================================================


def test_checkout_rolls_back_on_order_item_failure(monkeypatch) -> None:
    """If creating order items fails, checkout rolls back the transaction."""
    from sqlalchemy.exc import IntegrityError

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> SimpleNamespace:
            return make_cart(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_cart_id(self, cart_id: int) -> list[SimpleNamespace]:
            return [SimpleNamespace(product_id=1, quantity=1)]

    class ProductRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, product_id: int) -> SimpleNamespace:
            return make_product(
                id=product_id, price=Decimal("10.00"), stock_quantity=10
            )

        def decrement_stock_if_enough(self, product_id: int, quantity: int) -> bool:
            return True

    class BadOrderItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def create(self, item: object) -> object:
            raise IntegrityError("msg", {}, Exception("orig"))

    class OrderRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def create(self, order: object) -> object:
            order.id = 1  # type: ignore[attr-defined]
            return order

        def get_by_id(self, order_id: int) -> SimpleNamespace:
            return make_order(id=order_id, user_id=1)

    monkeypatch.setattr(use_cases, "CartRepository", CartRepo)
    monkeypatch.setattr(use_cases, "CartItemRepository", ItemRepo)
    monkeypatch.setattr(use_cases, "ProductRepository", ProductRepo)
    monkeypatch.setattr(use_cases, "OrderRepository", OrderRepo)
    monkeypatch.setattr(use_cases, "OrderItemRepository", BadOrderItemRepo)
    _stub_payment_use_case(monkeypatch)

    uow = DummyUoW()
    with pytest.raises(IntegrityError):
        use_cases.checkout(user_id=1, uow=uow)

    assert uow.rolled_back is True


def test_checkout_rolls_back_on_stock_decrement_failure(monkeypatch) -> None:
    """If stock decrement fails (not enough stock), checkout rolls back."""

    class CartRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_user_id(self, user_id: int) -> SimpleNamespace:
            return make_cart(id=1, user_id=user_id)

    class ItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_cart_id(self, cart_id: int) -> list[SimpleNamespace]:
            return [SimpleNamespace(product_id=1, quantity=1)]

    class ProductRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, product_id: int) -> SimpleNamespace:
            return make_product(id=product_id, price=Decimal("10.00"), stock_quantity=0)

        def decrement_stock_if_enough(self, product_id: int, quantity: int) -> bool:
            return False  # stock decrement fails

    class OrderRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def create(self, order: object) -> object:
            order.id = 1  # type: ignore[attr-defined]
            return order

        def get_by_id(self, order_id: int) -> SimpleNamespace:
            return make_order(id=order_id, user_id=1)

    class OrderItemRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def create(self, item: object) -> object:
            item.id = 1  # type: ignore[attr-defined]
            return item

    monkeypatch.setattr(use_cases, "CartRepository", CartRepo)
    monkeypatch.setattr(use_cases, "CartItemRepository", ItemRepo)
    monkeypatch.setattr(use_cases, "ProductRepository", ProductRepo)
    monkeypatch.setattr(use_cases, "OrderRepository", OrderRepo)
    monkeypatch.setattr(use_cases, "OrderItemRepository", OrderItemRepo)
    _stub_payment_use_case(monkeypatch)

    uow = DummyUoW()
    with pytest.raises(CoreValidationError, match="Insufficient stock"):
        use_cases.checkout(user_id=1, uow=uow)

    assert uow.rolled_back is True


# ======================================================================
# VALIDATION – schema tests
# ======================================================================


class TestOrderReadValidation:
    def test_valid_order_read(self) -> None:
        from datetime import datetime

        now = datetime.now(UTC)
        order = OrderRead(
            id=1,
            user_id=1,
            created_at=now,
            updated_at=now,
            items=[
                OrderItemRead(
                    id=1,
                    order_id=1,
                    product_id=2,
                    quantity=3,
                    price=Decimal("10.50"),
                    created_at=now,
                    updated_at=now,
                )
            ],
        )
        assert order.id == 1
        assert len(order.items) == 1
        assert order.items[0].price == Decimal("10.50")

    def test_order_read_without_items(self) -> None:
        from datetime import datetime

        now = datetime.now(UTC)
        order = OrderRead(id=1, user_id=1, created_at=now, updated_at=now)
        assert order.items == []

    def test_order_read_invalid_types(self) -> None:
        with pytest.raises(Exception):
            OrderItemRead(
                id=1,
                order_id=1,
                product_id=2,
                quantity="not-an-int",
                price="not-a-decimal",
                created_at="not-a-datetime",
                updated_at="not-a-datetime",
            )

    def test_order_read_missing_required(self) -> None:
        with pytest.raises(Exception):
            OrderRead(id=1, user_id=1, created_at=None, updated_at=None)  # type: ignore[arg-type]
