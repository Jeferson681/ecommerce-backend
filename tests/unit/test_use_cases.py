from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError

from backend.app.modules.payment import use_cases
from backend.app.modules.payment.schemas import PaymentWebhookPayload


class FakePayment:
    def __init__(self):
        self.id = 1
        self.order_id = 10
        self.user_id = 5
        self.provider_payment_id = "pp_1"
        self.status = "pending"
        self.failure_reason = None
        self.provider = "stripe"
        self.amount = Decimal("1.00")
        now = datetime.now(UTC)
        self.created_at = now
        self.updated_at = now


class FakeRepo:
    def __init__(self, payment):
        self._payment = payment

    def get_by_provider_payment_id(self, pid):
        return self._payment if pid == self._payment.provider_payment_id else None

    def update(self, payment):
        # pretend to persist
        self._payment = payment

    def get_by_id(self, id_):
        return self._payment if id_ == self._payment.id else None


class FakeUoW:
    def __init__(self, repo):
        self.session = None
        self._repo = repo

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        self.committed = True


def test_process_provider_webhook_success(monkeypatch):
    payment = FakePayment()
    repo = FakeRepo(payment)

    # monkeypatch the PaymentRepository used inside use_cases
    monkeypatch.setattr(use_cases, "PaymentRepository", lambda session: repo)

    uow = FakeUoW(repo)

    payload = PaymentWebhookPayload(
        provider_payment_id=payment.provider_payment_id,
        status="approved",
        failure_reason="ok",
    )

    result = use_cases.process_provider_webhook("stripe", payload, uow)

    assert result.status == "approved"
    assert result.failure_reason == "ok"


def test_process_provider_webhook_missing_provider_id_raises():
    with pytest.raises(PydanticValidationError):
        PaymentWebhookPayload(
            provider_payment_id="",
            status="approved",
        )
