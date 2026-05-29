"""Stripe Test Mode gateway implementation."""

from __future__ import annotations

import hashlib
import hmac
import time
from decimal import Decimal
from uuid import uuid4

from backend.app.modules.payment.gateway.base import PaymentGatewayResult


def verify_stripe_signature(
    payload: bytes, header: str | None, secret: str | None
) -> None:
    """Verify Stripe-style signature header.

    Raises ValueError on invalid signature. If `secret` is None verification is
    skipped (useful for local/test environments).
    """
    if not secret:
        return

    if not header:
        raise ValueError("Missing Stripe-Signature header")

    # header format: t=timestamp,v1=signature[,v1=...]
    try:
        parts = {
            k: v for k, v in (p.split("=", 1) for p in header.split(",") if "=" in p)
        }
    except Exception as err:
        raise ValueError("Invalid Stripe-Signature header format") from err

    t = parts.get("t")
    sig = parts.get("v1")
    if t is None or sig is None:
        raise ValueError("Invalid Stripe-Signature header")

    # optional timestamp tolerance (5 minutes)
    try:
        ts = int(t)
    except Exception as err:
        raise ValueError("Invalid timestamp in Stripe-Signature") from err

    if abs(time.time() - ts) > 300:
        raise ValueError("Stale Stripe webhook signature")

    signed_payload = f"{t}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()

    # compare in constant time
    if not hmac.compare_digest(expected, sig):
        raise ValueError("Invalid Stripe webhook signature")


class StripeGateway:
    name = "stripe"

    def process_payment(
        self,
        *,
        order_id: int,
        user_id: int,
        amount: Decimal,
        idempotency_key: str | None = None,
    ) -> PaymentGatewayResult:
        amount_cents = int((amount * 100).to_integral_value())
        idempotency_suffix = f"_{idempotency_key[:8]}" if idempotency_key else ""

        return PaymentGatewayResult(
            provider_payment_id=(
                f"pi_test_{order_id}_{user_id}_{amount_cents}{idempotency_suffix}_"
                f"{uuid4().hex}"
            ),
            status="approved",
            failure_reason=None,
        )
