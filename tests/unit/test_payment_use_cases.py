from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from sqlalchemy.orm import Session

from backend.app.modules.payment import services
from backend.app.uow.unit_of_work import UnitOfWork


class DummyUoW(UnitOfWork):
    def __init__(self) -> None:
        super().__init__(lambda: Mock(spec=Session))

        self.committed = False
        self.rolled_back = False

        self.attach(Mock(spec=Session))

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def flush(self) -> None:
        pass


def test_process_payment_happy_path(monkeypatch) -> None:
    uow = DummyUoW()

    class PaymentRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def create(self, payment: object):
            payment.id = 1  # type: ignore[attr-defined]

            from datetime import UTC, datetime

            now = datetime.now(UTC)

            payment.created_at = now  # type: ignore[attr-defined]
            payment.updated_at = now  # type: ignore[attr-defined]

            return payment

        def get_by_id(self, payment_id: int):
            from datetime import UTC, datetime

            now = datetime.now(UTC)

            return SimpleNamespace(
                id=payment_id,
                order_id=1,
                user_id=1,
                amount=Decimal("10.00"),
                status="pending",
                provider="stripe",
                provider_payment_id=None,
                failure_reason=None,
                created_at=now,
                updated_at=now,
            )

    class Gateway:
        name = "stripe"

        def process_payment(
            self,
            *args,
            **kwargs,
        ):
            from backend.app.modules.payment.gateway.base import (
                PaymentGatewayResult,
            )

            return PaymentGatewayResult(
                provider_payment_id="pi_1",
                status="approved",
                failure_reason=None,
            )

    monkeypatch.setattr(
        services,
        "PaymentRepository",
        lambda session: PaymentRepo(session),
    )

    payload = services.create_payment(
        order_id=1,
        user_id=1,
        amount=Decimal("10.00"),
        uow=uow,
        provider="stripe",
    )

    result = services.process_payment(
        payment_id=payload.id,
        payment_method_id="pm_1",
        uow=uow,
        gateway=Gateway(),  # type: ignore
        idempotency_key="key-123",
    )

    assert result.id == 1
    assert result.provider_payment_id == "pi_1"
    assert result.status == "approved"
