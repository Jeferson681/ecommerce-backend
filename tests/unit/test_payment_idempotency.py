from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from backend.app.modules.payment import use_cases
from backend.app.modules.payment.gateway.stripe_gateway import StripeGateway
from backend.app.modules.payment.schemas import PaymentRead


def test_process_payment_replays_raw_payload_once(monkeypatch):
    class DummyRepo:
        def __init__(self, session: object) -> None:
            self.session = session

    raw = {
        "id": 10,
        "order_id": 20,
        "user_id": 30,
        "amount": Decimal("19.90"),
        "status": "approved",
        "provider": "stripe",
        "provider_payment_id": "pi_123",
        "failure_reason": None,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0, 0),
    }
    calls = {"try_replay": 0}

    monkeypatch.setattr(use_cases, "PaymentRepository", DummyRepo)
    monkeypatch.setattr(use_cases, "OrderRepository", DummyRepo)
    monkeypatch.setattr(use_cases, "IdempotencyRepository", DummyRepo)

    def fake_try_replay(*, repository, key, user_id):
        calls["try_replay"] += 1
        return raw

    monkeypatch.setattr(use_cases, "try_replay", fake_try_replay)

    result = use_cases.process_payment(
        SimpleNamespace(
            session=object(),
            flush=lambda: None,
            commit=lambda: None,
            rollback=lambda: None,
        ),
        gateway=StripeGateway(),
        requesting_user_id=30,
        idempotency_key="pay-1",
        request_hash="hash-1",
    )

    assert calls["try_replay"] == 1
    assert result == PaymentRead.model_validate(raw)
