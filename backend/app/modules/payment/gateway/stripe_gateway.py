"""Stripe gateway implementation."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from decimal import Decimal

import stripe

from backend.app.core.config import settings
from backend.app.modules.payment.domain.models import PaymentStatus
from backend.app.modules.payment.gateway.base import (
    PaymentGatewayResult,
    PaymentRequest,
    PaymentWebhookPayload,
)

logger = logging.getLogger(__name__)


class StripeGateway:
    """Stripe PaymentIntent gateway."""

    name = "stripe"

    def __init__(self) -> None:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def process_payment(
        self,
        *,
        request: PaymentRequest,
        idempotency_key: str | None = None,
    ) -> PaymentGatewayResult:
        """
        Process a payment.

        Real Stripe mode:
            Requires STRIPE_SECRET_KEY and payment_method_id in
            ``request.provider_data``.

        Local mode:
            Uses deterministic mock when no Stripe key exists.
        """
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe secret key is not configured")

        payment_method_id = (
            request.provider_data.get("payment_method_id")
            if request.provider_data
            else None
        )

        if not payment_method_id:
            return PaymentGatewayResult(
                provider_payment_id=None,
                status=PaymentStatus.FAILED,
                failure_reason="payment_method_id is required",
            )

        return self._create_payment_intent(
            amount=request.amount,
            payment_method_id=payment_method_id,
            idempotency_key=idempotency_key,
        )

    def process_webhook(
        self,
        *,
        payload_bytes: bytes,
        signature: str | None = None,
    ) -> PaymentWebhookPayload:
        """Process a Stripe webhook.

        Sync payment state with Stripe API.
        """
        self._verify_stripe_signature(
            payload=payload_bytes,
            signature=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )

        event = json.loads(payload_bytes)

        payment_intent = event["data"]["object"]

        return PaymentWebhookPayload(
            provider_payment_id=payment_intent["id"],
            status=self._map_status(payment_intent["status"]),
            provider_status=payment_intent["status"],
            failure_reason=self._extract_webhook_failure_reason(
                payment_intent,
            ),
        )

    def _create_payment_intent(
        self,
        *,
        amount: Decimal,
        payment_method_id: str,
        idempotency_key: str | None,
    ) -> PaymentGatewayResult:
        """Create and confirm a Stripe PaymentIntent."""

        amount_cents = int((amount * 100).to_integral_value())

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="brl",
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",
                },
                idempotency_key=idempotency_key,
            )

            return PaymentGatewayResult(
                provider_payment_id=intent.id,
                status=self._map_status(intent.status),
                failure_reason=self._extract_failure_reason(intent),
                provider_status=intent.status,
                provider_reference=None,
            )

        except stripe.CardError as err:
            return PaymentGatewayResult(
                provider_payment_id=None,
                status=PaymentStatus.FAILED,
                failure_reason=err.user_message,
                provider_status=None,
                provider_reference=None,
            )

        except stripe.StripeError as err:
            return PaymentGatewayResult(
                provider_payment_id=None,
                status=PaymentStatus.FAILED,
                failure_reason=str(err),
                provider_status=None,
                provider_reference=None,
            )

    def _map_status(
        self,
        stripe_status: str,
    ) -> PaymentStatus:
        mapping: dict[str, PaymentStatus] = {
            "succeeded": PaymentStatus.APPROVED,
            "processing": PaymentStatus.PENDING,
            "requires_action": PaymentStatus.PENDING,
            "requires_capture": PaymentStatus.PENDING,
            "requires_confirmation": PaymentStatus.PENDING,
            "requires_payment_method": PaymentStatus.FAILED,
            "canceled": PaymentStatus.CANCELLED,
        }

        return mapping.get(
            stripe_status,
            PaymentStatus.FAILED,
        )

    @staticmethod
    def _extract_failure_reason(intent: stripe.PaymentIntent) -> str | None:
        error = getattr(intent, "last_payment_error", None)

        if error is None:
            return None

        return getattr(error, "message", None)

    @staticmethod
    def _extract_webhook_failure_reason(payment_intent: dict) -> str | None:
        """Extract failure reason from a Stripe webhook payload (parsed JSON dict).

        The webhook flow uses a dict (from json.loads), not a stripe.PaymentIntent
        object, so all accesses use dict key syntax.
        """
        if payment_intent.get("status") != "succeeded":
            return f"PaymentIntent status is {payment_intent.get('status')}"

        return None

    def _verify_stripe_signature(
        self,
        payload: bytes,
        signature: str | None,
        secret: str | None,
    ) -> None:
        """Validate Stripe webhook signature.

        Uses manual HMAC verification for portability (avoids relying on
        the SDK's internal event parsing).

        Security (fail-fast):
        - If secret is missing and DEBUG=False → raise ValueError (production block).
        - If secret is missing and DEBUG=True → log warning and allow (local dev only).
        - If signature is missing → raise ValueError.
        - If signature is invalid → raise ValueError.
        """

        # --- Fail-fast: webhook secret is mandatory in production ---
        if not secret:
            if settings.DEBUG:
                logger.warning(
                    "STRIPE_WEBHOOK_SECRET is not configured. "
                    "Webhook signature verification DISABLED (DEBUG mode). "
                    "This is unsafe for production."
                )
                return
            raise ValueError(
                "STRIPE_WEBHOOK_SECRET is not configured. "
                "Webhook processing is disabled in production without a secret."
            )

        if not signature:
            raise ValueError("Missing Stripe-Signature header")

        # header format: t=timestamp,v1=signature[,v1=...]
        try:
            parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
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
