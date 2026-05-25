from __future__ import annotations

from decimal import Decimal

import pytest

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.modules.payment import payment_service as svc


def test_validate_idempotency_input_accepts_both_or_none() -> None:
    # both None ok
    svc.validate_idempotency_input(None, None)

    # both present ok
    svc.validate_idempotency_input("key", "hash")


def test_validate_idempotency_input_rejects_mismatch() -> None:
    with pytest.raises(ValidationError):
        svc.validate_idempotency_input("only-key", None)


def test_calculate_order_total_uses_order_item_prices() -> None:
    order = type("O", (), {})()
    item = type("I", (), {})()
    item.price = Decimal("12.50")
    item.quantity = 2
    order.items = [item]

    total = svc.calculate_order_total(order)
    assert total == Decimal("25.00")


def test_assert_requester_can_access_order_owner_and_admin(monkeypatch) -> None:
    order = type("O", (), {})()
    order.user_id = 1

    uow = type("U", (), {})()
    uow.session = object()

    # owner ok
    svc.assert_requester_can_access_order(order, 1, uow)

    # admin ok
    class UserRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, user_id: int):
            return type("U", (), {"role": "admin"})()

    monkeypatch.setattr(svc, "UserRepository", lambda s: UserRepo(s))

    svc.assert_requester_can_access_order(order, 999, uow)


def test_assert_requester_can_access_order_raises_when_missing_user() -> None:
    order = type("O", (), {})()
    order.user_id = 1

    uow = type("U", (), {})()
    uow.session = object()

    with pytest.raises(NotFoundError):
        svc.assert_requester_can_access_order(order, None, uow)
