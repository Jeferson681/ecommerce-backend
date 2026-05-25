from __future__ import annotations

from backend.app.modules.payment import payment_service as svc


def test_try_replay_payment_returns_none_when_no_key():
    assert (
        svc.try_replay_payment(
            repository=type("R", (), {})(), idempotency_key=None, user_id=None
        )
        is None
    )


def test_reserve_payment_idempotency_noops_when_missing_params():
    # should not raise when idempotency not provided
    svc.reserve_payment_idempotency(
        repository=type("R", (), {})(),
        idempotency_key=None,
        request_hash=None,
        user_id=None,
    )


def test_persist_payment_idempotent_response_noops_when_missing():
    # provide a payment repo that returns None for get_by_id
    class FakePaymentRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_id(self, payment_id: int):
            return None

    svc.persist_payment_idempotent_response(
        repository=type("R", (), {})(),
        payment_repository=FakePaymentRepo(None),
        payment_id=1,
        idempotency_key=None,
        user_id=None,
    )
