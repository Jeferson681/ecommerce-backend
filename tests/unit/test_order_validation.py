from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.modules.order.schemas import OrderItemRead, OrderRead


def test_order_item_read_invalid_types():
    with pytest.raises(ValidationError):
        OrderItemRead(
            id=1,
            order_id=1,
            product_id=2,
            quantity="not-an-int",
            price="not-a-decimal",
            created_at="not-a-datetime",
            updated_at="not-a-datetime",
        )


def test_order_read_missing_required():
    with pytest.raises(ValidationError):
        OrderRead(id=1, user_id=1, created_at=None, updated_at=None)
