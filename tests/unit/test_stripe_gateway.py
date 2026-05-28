import hashlib
import hmac
import time

import pytest

from backend.app.modules.payment.gateway import stripe_gateway


def test_verify_signature_valid():
    payload = b'{"test":1}'
    secret = "test_secret"
    ts = str(int(time.time()))
    signed_payload = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"

    # Should not raise
    stripe_gateway.verify_stripe_signature(payload, header, secret)


def test_missing_header_raises():
    with pytest.raises(ValueError):
        stripe_gateway.verify_stripe_signature(b"{}", None, "secret")


def test_invalid_signature_raises():
    header = "t=123,v1=bad"
    with pytest.raises(ValueError):
        stripe_gateway.verify_stripe_signature(b"{}", header, "secret")


def test_stale_signature_raises():
    payload = b"{}"
    secret = "s"
    ts = str(int(time.time()) - 1000)
    signed_payload = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"

    with pytest.raises(ValueError):
        stripe_gateway.verify_stripe_signature(payload, header, secret)


def test_skip_verification_when_secret_none():
    # no exception should be raised when secret is falsy
    stripe_gateway.verify_stripe_signature(b"{}", None, None)


def test_invalid_header_format_raises():
    # header without '=' pairs should raise
    with pytest.raises(ValueError):
        stripe_gateway.verify_stripe_signature(b"{}", "badheader", "s")


def test_invalid_timestamp_raises():
    payload = b"{}"
    secret = "s"
    header = "t=notint,v1=abc"
    with pytest.raises(ValueError):
        stripe_gateway.verify_stripe_signature(payload, header, secret)
