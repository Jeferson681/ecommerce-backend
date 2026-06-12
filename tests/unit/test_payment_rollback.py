from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app.modules.payment import use_cases


class BadGateway:
    name = "bad"

    def process_payment(self, *, request, idempotency_key=None):
        raise RuntimeError("gateway down")


def test_process_payment_rolls_back_on_exception(monkeypatch) -> None:
    class OrderRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, order_id: int):
            return SimpleNamespace(
                id=1,
                user_id=1,
                items=[SimpleNamespace(price=Decimal("1.00"), quantity=1)],
            )

    class PaymentRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def create(self, payment: object):
            payment.id = 1
            return payment

        def update(self, payment: object):
            return payment

    class IdempotencyRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_key(self, key: str, user_id: int | None = None):
            return None

        def claim(self, record: object):
            return (record, True)

    monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))
    monkeypatch.setattr(use_cases, "OrderRepository", lambda s: OrderRepo(s))
    monkeypatch.setattr(
        use_cases, "IdempotencyRepository", lambda s: IdempotencyRepo(s)
    )

    class Uow:
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

    uow = Uow()

    with pytest.raises(RuntimeError):
        use_cases.process_payment(
            PaymentCreate(order_id=1), uow, requesting_user_id=1, gateway=BadGateway()
        )

    assert uow.rolled_back is True
