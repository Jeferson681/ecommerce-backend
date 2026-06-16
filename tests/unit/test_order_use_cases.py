# ruff: noqa: B017

"""Comprehensive tests for Order use cases."""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.modules.order import use_cases
from backend.app.modules.order.schemas import OrderItemRead, OrderRead

from .conftest import DummyUoW, make_order


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
                return make_order(id=order_id, user_id=2)

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


class TestGetOrderSadPath:
    def test_get_order_raises_not_found_when_missing(self, monkeypatch) -> None:

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, order_id: int) -> None:
                return None

        monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))

        with pytest.raises(NotFoundError, match="Order not found"):
            use_cases.get_order(order_id=999, user_id=1, uow=DummyUoW())

    def test_get_order_raises_for_non_owner_non_admin(self, monkeypatch) -> None:

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, order_id: int) -> SimpleNamespace:
                return make_order(id=order_id, user_id=2)

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

        with pytest.raises(NotFoundError, match="Order not found"):
            use_cases.get_order(
                order_id=1, user_id=3, uow=DummyUoW(), requesting_user_id=3
            )

    def test_list_orders_empty(self, monkeypatch) -> None:

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_user_id(self, user_id: int) -> list:
                return []

        monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))

        orders = use_cases.list_orders(user_id=999, uow=DummyUoW())
        assert orders == []


class TestOrderReadValidation:
    def test_valid_order_read(self) -> None:
        from datetime import datetime

        now = datetime.now(UTC)
        order = OrderRead(
            id=1,
            user_id=1,
            status="pending",
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
        order = OrderRead(
            id=1, user_id=1, status="pending", created_at=now, updated_at=now
        )
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
            OrderRead(id=1, user_id=1, status=None, created_at=None, updated_at=None)
