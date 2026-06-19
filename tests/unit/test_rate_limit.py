"""Tests for rate limiting configuration."""

import asyncio

from slowapi.errors import RateLimitExceeded

from backend.app.core.rate_limit import limiter, rate_limit_exceeded_handler


def test_limiter_initialized():
    """Limiter should be initialized with get_remote_address."""
    assert limiter is not None
    assert limiter._key_func is not None


def test_rate_limit_exceeded_handler_returns_429():
    """Handler should return JSONResponse with 429 status."""
    from fastapi.responses import JSONResponse

    request = None  # Not used by handler

    # Build a minimal limit-like object accepted by RateLimitExceeded
    class _FakeLimit:
        error_message = None
        limit = "5/minute"

    exc = RateLimitExceeded(_FakeLimit())

    response = asyncio.run(rate_limit_exceeded_handler(request, exc))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 429
    body = response.body
    assert b"RateLimitExceeded" in body
    assert b"Too many requests" in body
