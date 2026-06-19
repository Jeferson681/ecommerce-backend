"""Unit tests for Stripe webhook signature verification fail-fast behaviour.

Covers:
- secret ausente (missing secret) → DEBUG=True allows / DEBUG=False blocks
- assinatura inválida (invalid signature) → raises ValueError
- assinatura válida (valid signature) → passes
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from unittest.mock import patch

import pytest

# Ensure JWT_SECRET_KEY is available for Settings validation
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")

from backend.app.modules.payment.gateway.stripe_gateway import StripeGateway


def _valid_signature(payload: bytes, secret: str) -> str:
    ts = str(int(time.time()))
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _expired_signature(payload: bytes, secret: str) -> str:
    ts = str(int(time.time()) - 600)  # 10 minutes ago → stale
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


class TestWebhookSecretMissing:
    """STRIPE_WEBHOOK_SECRET ausente."""

    def test_missing_secret_in_production_raises_error(self) -> None:
        """Quando DEBUG=False, secret ausente deve levantar ValueError (503/400)."""
        gateway = StripeGateway()
        payload = json.dumps({"dummy": True}).encode()

        with patch("backend.app.core.config.settings.DEBUG", False):
            with pytest.raises(
                ValueError, match="STRIPE_WEBHOOK_SECRET is not configured"
            ):
                gateway._verify_stripe_signature(
                    payload=payload,
                    signature=None,
                    secret=None,
                )

    def test_missing_secret_in_debug_allows(self) -> None:
        """Quando DEBUG=True, secret ausente deve permitir (apenas dev local)."""
        gateway = StripeGateway()
        payload = json.dumps({"dummy": True}).encode()

        with patch("backend.app.core.config.settings.DEBUG", True):
            # Não deve levantar exceção
            gateway._verify_stripe_signature(
                payload=payload,
                signature=None,
                secret=None,
            )


class TestWebhookSignatureInvalid:
    """Assinatura inválida."""

    def test_missing_signature_header_raises_error(self) -> None:
        """Header Stripe-Signature ausente."""
        gateway = StripeGateway()
        payload = json.dumps({"dummy": True}).encode()

        with pytest.raises(ValueError, match="Missing Stripe-Signature header"):
            gateway._verify_stripe_signature(
                payload=payload,
                signature=None,
                secret="whsec_test_secret",
            )

    def test_wrong_signature_value_raises_error(self) -> None:
        """Assinatura não corresponde ao payload."""
        gateway = StripeGateway()
        payload = json.dumps({"dummy": True}).encode()
        # Use current timestamp but wrong HMAC signature
        ts = str(int(time.time()))
        wrong_sig = f"t={ts},v1=0000000000000000000000000000000000000000000000000000000000000000"

        with pytest.raises(ValueError, match="Invalid Stripe webhook signature"):
            gateway._verify_stripe_signature(
                payload=payload,
                signature=wrong_sig,
                secret="whsec_test_secret",
            )

    def test_stale_timestamp_raises_error(self) -> None:
        """Timestamp expirado (>5 minutos)."""
        gateway = StripeGateway()
        payload = json.dumps({"dummy": True}).encode()
        expired_sig = _expired_signature(payload, "whsec_test_secret")

        with pytest.raises(ValueError, match="Stale Stripe webhook signature"):
            gateway._verify_stripe_signature(
                payload=payload,
                signature=expired_sig,
                secret="whsec_test_secret",
            )

    def test_malformed_signature_header_raises_error(self) -> None:
        """Formato inválido do header."""
        gateway = StripeGateway()
        payload = json.dumps({"dummy": True}).encode()

        with pytest.raises(ValueError, match="Invalid Stripe-Signature header"):
            gateway._verify_stripe_signature(
                payload=payload,
                signature="garbage_without_equals",
                secret="whsec_test_secret",
            )


class TestWebhookSignatureValid:
    """Assinatura válida."""

    def test_valid_signature_passes(self) -> None:
        """Assinatura correta com secret correto."""
        gateway = StripeGateway()
        payload = json.dumps({"dummy": True}).encode()
        valid_sig = _valid_signature(payload, "whsec_test_secret")

        # Não deve levantar exceção
        gateway._verify_stripe_signature(
            payload=payload,
            signature=valid_sig,
            secret="whsec_test_secret",
        )

    def test_valid_signature_with_different_secret_fails(self) -> None:
        """Assinatura com secret diferente deve falhar."""
        gateway = StripeGateway()
        payload = json.dumps({"dummy": True}).encode()
        # Assinatura criada com um secret diferente
        valid_sig = _valid_signature(payload, "whsec_other_secret")

        with pytest.raises(ValueError, match="Invalid Stripe webhook signature"):
            gateway._verify_stripe_signature(
                payload=payload,
                signature=valid_sig,
                secret="whsec_test_secret",
            )
