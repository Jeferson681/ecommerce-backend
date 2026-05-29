from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.routers import payment_webhook as payment_webhook_router
from backend.app.core.database import Base, engine
from backend.app.main import app
from backend.app.modules.order.domain.models import Order
from backend.app.modules.payment.domain.models import Payment
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
    signed_payload = f"{timestamp}.".encode() + payload_bytes
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def test_payment_webhook_updates_existing_payment() -> None:
    session = SessionLocal()

    user = User(
        first_name="Ana",
        last_name="Silva",
        email="ana-payment@mail.com",
        password_hash="hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    order = Order(user_id=user.id)
    session.add(order)
    session.commit()
    session.refresh(order)

    payment = Payment(
        order_id=order.id,
        user_id=user.id,
        amount=Decimal("10.00"),
        status="pending",
        provider="stripe",
        provider_payment_id="pi_webhook_123",
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    session.close()

    secret = "whsec_test_secret"
    payment_webhook_router.settings.STRIPE_WEBHOOK_SECRET = secret

    payload = {
        "provider_payment_id": payment.provider_payment_id,
        "status": "approved",
    }
    body = json.dumps(payload).encode()
    signature = _sign_payload(body, secret)

    resp = client.post(
        "/payments/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
            "X-Payment-Provider": "stripe",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    verify_session = SessionLocal()
    updated = verify_session.get(Payment, payment.id)
    assert updated is not None
    assert updated.status == "approved"
    verify_session.close()


def test_payment_webhook_rejects_invalid_signature() -> None:
    secret = "whsec_test_secret"
    payment_webhook_router.settings.STRIPE_WEBHOOK_SECRET = secret

    payload = {"provider_payment_id": "pi_missing", "status": "approved"}
    body = json.dumps(payload).encode()

    resp = client.post(
        "/payments/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "t=1,v1=deadbeef",
            "X-Payment-Provider": "stripe",
        },
    )

    assert resp.status_code == 400
