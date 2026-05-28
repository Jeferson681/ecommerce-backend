from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app.core.exceptions import NotFoundError, ValidationError
from backend.app.modules.payment import payment_service as svc, use_cases
from backend.app.modules.payment.schemas import PaymentCreate


def test_process_payment_rejects_mismatched_idempotency_inputs(monkeypatch) -> None:
    class GuardedRepo:
        def __init__(self, session: object) -> None:
            raise AssertionError(
                "repositories should not be instantiated before validation"
            )

    monkeypatch.setattr(use_cases, "PaymentRepository", GuardedRepo)
    monkeypatch.setattr(use_cases, "OrderRepository", GuardedRepo)
    monkeypatch.setattr(use_cases, "IdempotencyRepository", GuardedRepo)

    with pytest.raises(ValidationError):
        use_cases.process_payment(
            PaymentCreate(order_id=1),
            SimpleNamespace(
                session=object(),
                flush=lambda: None,
                commit=lambda: None,
                rollback=lambda: None,
            ),
            idempotency_key="only-key",
            request_hash=None,
        )


def test_calculate_order_total_uses_order_item_prices() -> None:
    order = type("O", (), {})()
    item = type("I", (), {})()
    item.price = Decimal("12.50")
    item.quantity = 2
    order.items = [item]

    total = use_cases.calculate_order_total(order)
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
