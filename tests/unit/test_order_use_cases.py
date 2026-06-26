# ruff: noqa: B017

"""Comprehensive tests for Order use cases."""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.modules.order import services
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

        monkeypatch.setattr(services, "OrderRepository", lambda s: OrderRepo(s))

        order = services.get_order(order_id=1, user_id=1, uow=DummyUoW())
        assert order.id == 1
        assert order.user_id == 1

    def test_get_order_owner_only(self, monkeypatch) -> None:
        """Only the owner can retrieve an order."""

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, order_id: int) -> SimpleNamespace:
                return make_order(id=order_id, user_id=1)

        monkeypatch.setattr(services, "OrderRepository", lambda s: OrderRepo(s))

        # Owner can access
        result = services.get_order(order_id=1, user_id=1, uow=DummyUoW())
        assert result.id == 1

        # Non-owner gets NotFoundError
        with pytest.raises(NotFoundError):
            services.get_order(order_id=1, user_id=2, uow=DummyUoW())

    def test_list_orders_returns_user_orders(self, monkeypatch) -> None:
        """Listing orders returns all orders for the authenticated user."""

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def list_by_user(self, user_id: int) -> list[SimpleNamespace]:
                return [
                    make_order(id=1, user_id=user_id),
                    make_order(id=2, user_id=user_id),
                ]

        monkeypatch.setattr(services, "OrderRepository", lambda s: OrderRepo(s))

        orders = services.list_orders(user_id=1, uow=DummyUoW())
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

        monkeypatch.setattr(services, "OrderRepository", lambda s: OrderRepo(s))

        with pytest.raises(NotFoundError, match="Order not found"):
            services.get_order(order_id=999, user_id=1, uow=DummyUoW())

    def test_get_order_raises_for_non_owner(self, monkeypatch) -> None:

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def get_by_id(self, order_id: int) -> SimpleNamespace:
                return make_order(id=order_id, user_id=2)

        monkeypatch.setattr(services, "OrderRepository", lambda s: OrderRepo(s))

        with pytest.raises(NotFoundError, match="Order not found"):
            services.get_order(order_id=1, user_id=3, uow=DummyUoW())

    def test_list_orders_empty(self, monkeypatch) -> None:

        class OrderRepo:
            def __init__(self, session: object) -> None:
                self.session = session

            def list_by_user(self, user_id: int) -> list:
                return []

        monkeypatch.setattr(services, "OrderRepository", lambda s: OrderRepo(s))

        orders = services.list_orders(user_id=999, uow=DummyUoW())
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
