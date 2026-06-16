"""Shared fixtures and utilities for unit tests."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest


class DummyUoW:
    """A lightweight fake Unit of Work for unit tests.

    Tests should assert on ``committed`` and ``rolled_back`` after
    exercising the use case under test.
    """

    def __init__(self) -> None:
        self.session = object()
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def flush(self) -> None:
        return None


@pytest.fixture
def uow() -> DummyUoW:
    return DummyUoW()


# ---------------------------------------------------------------------------
# Helper – build a minimal user-like SimpleNamespace
# ---------------------------------------------------------------------------
def make_user(**overrides: Any) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = dict(
        id=1,
        first_name="Ana",
        last_name="Silva",
        email="ana@mail.com",
        password_hash="hashed:secret",
        is_active=True,
        role="user",
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Helper – build a minimal cart-like SimpleNamespace
# ---------------------------------------------------------------------------
def make_cart(**overrides: Any) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = dict(
        id=1,
        user_id=1,
        items=[],
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Helper – build a minimal cart-item-like SimpleNamespace
# ---------------------------------------------------------------------------
def make_cart_item(**overrides: Any) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = dict(
        id=1,
        cart_id=1,
        product_id=2,
        quantity=1,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Helper – build a minimal product-like SimpleNamespace
# ---------------------------------------------------------------------------
def make_product(**overrides: Any) -> SimpleNamespace:
    from decimal import Decimal

    defaults = dict(
        id=1,
        name="Test Product",
        price=Decimal("10.00"),
        stock_quantity=10,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Helper – build a minimal order-like SimpleNamespace
# ---------------------------------------------------------------------------
def make_order(**overrides: Any) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = dict(
        id=1,
        user_id=1,
        status="pending",
        items=[],
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)
