"""Integration tests for webhook idempotency (duplicate delivery protection).

Validates that Stripe webhook events delivered twice do not create
duplicate payments or orders.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app

client = TestClient(app)

TEST_SECRET = "whsec_test_idempotency"


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    settings.STRIPE_WEBHOOK_SECRET = None
    Base.metadata.drop_all(bind=engine)


def _sign_payload(payload: dict) -> tuple[bytes, str]:
    """Create a signed Stripe webhook payload."""
    payload_bytes = json.dumps(payload).encode()
    ts = str(int(time.time()))
    signed = f"{ts}.".encode() + payload_bytes
    sig = hmac.new(TEST_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"
    return payload_bytes, header


def _create_order_and_payment_in_db(
    provider_payment_id: str,
) -> dict:
    """Create an order and payment directly in DB for webhook testing."""
    db = SessionLocal()
    try:
        from backend.app.modules.order.domain.models import Order
        from backend.app.modules.payment.domain.models import (
            Payment,
            PaymentStatus,
        )
        from backend.app.modules.user.domain.models import User

        if db.get(User, 999) is None:
            db.add(
                User(
                    id=999,
                    first_name="Webhook",
                    last_name="User",
                    email="webhook-user-999@example.com",
                    password_hash="x",
                )
            )
            db.commit()

        order = Order(user_id=999, status="pending")
        db.add(order)
        db.flush()
        db.refresh(order)

        payment = Payment(
            order_id=order.id,
            user_id=999,
            amount=Decimal("50.00"),
            status=PaymentStatus.PENDING,
            provider="stripe",
            provider_payment_id=provider_payment_id,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return {"order_id": order.id, "payment_id": payment.id}
    finally:
        db.close()


class TestDuplicateWebhookDelivery:
    """Duplicate webhook events should be idempotent."""

    def test_duplicate_payment_succeeded_is_idempotent(self) -> None:
        """Sending payment_intent.succeeded twice should not duplicate state."""
        settings.STRIPE_WEBHOOK_SECRET = TEST_SECRET

        provider_id = f"pi_dup_success_{int(time.time())}"
        records = _create_order_and_payment_in_db(provider_id)
        payment_id = records["payment_id"]

        event_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": provider_id,
                    "status": "succeeded",
                    "amount": 5000,
                }
            },
        }

        # First delivery
        payload_bytes1, sig1 = _sign_payload(event_payload)
        resp1 = client.post(
            "/webhooks/stripe",
            content=payload_bytes1,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": sig1,
            },
        )
        assert resp1.status_code == 200, f"First delivery failed: {resp1.text}"

        # Verify payment is APPROVED and order is PAID after first delivery
        db = SessionLocal()
        try:
            from backend.app.modules.order.domain.models import Order
            from backend.app.modules.payment.domain.models import Payment, PaymentStatus

            payment1 = db.get(Payment, payment_id)
            assert payment1 is not None
            assert payment1.status == PaymentStatus.APPROVED

            order1 = db.get(Order, payment1.order_id)
            assert order1 is not None
            assert order1.status == "paid"
        finally:
            db.close()

        # Second delivery (same event, same provider_payment_id)
        payload_bytes2, sig2 = _sign_payload(event_payload)
        resp2 = client.post(
            "/webhooks/stripe",
            content=payload_bytes2,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": sig2,
            },
        )
        assert resp2.status_code == 200, f"Second delivery failed: {resp2.text}"

        # Verify no duplicate payments were created
        db2 = SessionLocal()
        try:
            from backend.app.modules.payment.repositories.payment_repository import (
                PaymentRepository,
            )

            pay_repo = PaymentRepository(db2)
            payments_for_order = pay_repo.get_by_order_id(records["order_id"])
            assert len(payments_for_order) == 1, (
                f"Expected 1 payment, got {len(payments_for_order)}"
            )
        finally:
            db2.close()

    def test_duplicate_payment_failed_is_idempotent(self) -> None:
        """Sending payment_intent.payment_failed twice should not duplicate state."""
        settings.STRIPE_WEBHOOK_SECRET = TEST_SECRET

        provider_id = f"pi_dup_fail_{int(time.time())}"
        records = _create_order_and_payment_in_db(provider_id)
        records["payment_id"]

        event_payload = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": provider_id,
                    "status": "failed",
                    "amount": 5000,
                    "last_payment_error": {
                        "message": "card_declined",
                    },
                }
            },
        }

        # First delivery
        payload_bytes1, sig1 = _sign_payload(event_payload)
        resp1 = client.post(
            "/webhooks/stripe",
            content=payload_bytes1,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": sig1,
            },
        )
        assert resp1.status_code == 200, f"First delivery failed: {resp1.text}"

        # Second delivery
        payload_bytes2, sig2 = _sign_payload(event_payload)
        resp2 = client.post(
            "/webhooks/stripe",
            content=payload_bytes2,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": sig2,
            },
        )
        assert resp2.status_code == 200, f"Second delivery failed: {resp2.text}"

        # Verify only one payment exists
        db = SessionLocal()
        try:
            from backend.app.modules.payment.repositories.payment_repository import (
                PaymentRepository,
            )

            pay_repo = PaymentRepository(db)
            payments_for_order = pay_repo.get_by_order_id(records["order_id"])
            assert len(payments_for_order) == 1
        finally:
            db.close()
