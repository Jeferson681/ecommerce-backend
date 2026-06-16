"""Payment webhook integration tests.

Tests the full webhook flow: Stripe-like payload → gateway processing →
payment lookup → payment update → order update.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings as app_settings
from backend.app.core.database import Base, engine
from backend.app.main import app
from backend.app.modules.order.domain.models import Order, OrderStatus
from backend.app.modules.payment.domain.models import Payment, PaymentStatus
from backend.app.modules.user.domain.models import User

client = TestClient(app)
SessionLocal: sessionmaker[Session]


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)
    global SessionLocal
    SessionLocal = sessionmaker(bind=engine, future=True)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    timestamp = str(int(time.time()))
    keyed_msg = f"{timestamp}.".encode() + payload_bytes
    signature = hmac.new(secret.encode(), keyed_msg, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def _create_fixtures(session) -> tuple[User, int, Payment]:
    user = User(
        first_name="Webhook",
        last_name="Test",
        email="webhook@test.com",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    order = Order(user_id=user.id)
    session.add(order)
    session.commit()
    session.refresh(order)
    order_id = order.id

    payment = Payment(
        order_id=order_id,
        user_id=user.id,
        amount=Decimal("25.00"),
        status=PaymentStatus.PENDING,
        provider="stripe",
        provider_payment_id="pi_webhook_e2e",
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    session.close()
    return user, order_id, payment


def test_webhook_updates_payment_and_order_on_approval() -> None:
    session = SessionLocal()
    _, order_id, payment = _create_fixtures(session)

    secret = "whsec_test_secret"
    app_settings.STRIPE_WEBHOOK_SECRET = secret

    payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": payment.provider_payment_id,
                "status": "succeeded",
            }
        },
    }
    body = json.dumps(payload).encode()
    signature = _sign_payload(body, secret)

    resp = client.post(
        "/webhooks/stripe",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert resp.status_code == 200
    assert resp.json() == {"received": True}

    verify_session = SessionLocal()
    updated_payment = verify_session.get(Payment, payment.id)
    assert updated_payment is not None
    assert updated_payment.status == PaymentStatus.APPROVED

    updated_order = verify_session.get(Order, order_id)
    assert updated_order is not None
    assert updated_order.status == OrderStatus.PAID
    verify_session.close()


def test_webhook_rejects_invalid_signature() -> None:
    secret = "whsec_test_secret"
    app_settings.STRIPE_WEBHOOK_SECRET = secret

    payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_irrelevant",
                "status": "succeeded",
            }
        },
    }
    body = json.dumps(payload).encode()

    resp = client.post(
        "/webhooks/stripe",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "t=1,v1=deadbeef",
        },
    )

    assert resp.status_code == 400


def test_webhook_returns_404_for_missing_payment() -> None:
    secret = "whsec_test_secret"
    app_settings.STRIPE_WEBHOOK_SECRET = secret

    payload = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_nonexistent",
                "status": "succeeded",
            }
        },
    }
    body = json.dumps(payload).encode()
    signature = _sign_payload(body, secret)

    resp = client.post(
        "/webhooks/stripe",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert resp.status_code == 404
