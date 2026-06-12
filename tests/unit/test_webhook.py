def test_process_provider_webhook_happy_and_errors(monkeypatch) -> None:
    uow = DummyUoW()

    class PaymentRepo:
        def __init__(self, session: object) -> None:
            self.session = session

        def get_by_provider_payment_id(self, provider_payment_id: str):
            from datetime import UTC, datetime

            now = datetime.now(UTC)

            if provider_payment_id == "exists":
                return SimpleNamespace(
                    id=1,
                    order_id=1,
                    user_id=1,
                    amount=Decimal("10.00"),
                    status="pending",
                    provider="stripe",
                    provider_payment_id=provider_payment_id,
                    failure_reason=None,
                    created_at=now,
                    updated_at=now,
                )
            return None

        def update(self, payment: object):
            return payment

        def get_by_id(self, payment_id: int):
            from datetime import UTC, datetime

            now = datetime.now(UTC)

            return SimpleNamespace(
                id=payment_id,
                order_id=1,
                user_id=1,
                amount=Decimal("10.00"),
                status="approved",
                provider="stripe",
                provider_payment_id="exists",
                failure_reason=None,
                created_at=now,
                updated_at=now,
            )

        class IdempotencyRepo:
            def __init__(self, session: object) -> None:
                self.session = session

        def get_by_key(self, key: str, user_id: int | None = None):
            return None

        def claim(self, record: object):
            return (record, True)

        def save_response(self, key: str, user_id: int, status: int, body: str):
            pass

        def delete_by_key(self, key: str, user_id: int) -> None:
            pass

    class Gateway:
        name = "stripe"

        def process_webhook(
            self,
            *payload_bytes,
            signature=None,
            idempotency_key=None,
        ):
            from backend.app.modules.payment.gateway.base import PaymentGatewayResult

            return PaymentGatewayResult(
                provider_payment_id="pi_1", status="approved", failure_reason=None
            )

    monkeypatch.setattr(use_cases, "PaymentRepository", lambda s: PaymentRepo(s))

    # happy path
    payload = process_gateway_webhook(
        gateway=Gateway(),
        payload_bytes=payload_bytes,
        signature=None,
        idempotency_key=None,
    )
    result = use_cases.process_provider_webhook("stripe", payload, uow)
    assert result.status == "approved"

    # invalid payload is rejected by the schema at the boundary
    with pytest.raises(PydanticValidationError):
        PaymentWebhookPayload(status="approved")

    # missing payment
    with pytest.raises(NotFoundError):
        use_cases.process_provider_webhook(
            "stripe",
            PaymentWebhookPayload(
                provider_payment_id="nope",
                status="approved",
            ),
            uow,
        )
