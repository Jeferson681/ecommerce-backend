"""Integration tests for rate limiting on /auth/token.

Tests the real slowapi middleware behavior by sending sequential requests.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.core.database import Base, engine
from backend.app.main import app

client = TestClient(app)


def setup_module(module: object) -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module(module: object) -> None:
    Base.metadata.drop_all(bind=engine)


class TestRateLimitEnforcement:
    """Real rate limiting behavior on /auth/token."""

    def test_rate_limit_blocks_after_limit_exceeded(self) -> None:
        """After 5 requests to /auth/token, the 6th should return 429."""
        # Create a user first
        import random

        uid = random.randint(10000, 99999)
        email = f"ratelimit-{uid}@mail.com"
        create_resp = client.post(
            "/users",
            json={
                "first_name": "Rate",
                "last_name": "Limit",
                "email": email,
                "password": "Password123!",
            },
        )
        assert create_resp.status_code == 201

        payload = {"email": email, "password": "Password123!"}

        # Send 5 requests — all should be allowed
        for i in range(5):
            resp = client.post("/auth/token", json=payload)
            assert resp.status_code == 200, (
                f"Request {i + 1} should be 200, got {resp.status_code}"
            )

        # 6th request should be rate limited
        resp = client.post("/auth/token", json=payload)
        assert resp.status_code == 429, f"Expected 429, got {resp.status_code}"
        body = resp.json()
        assert "error" in body
        assert "RateLimitExceeded" in body.get("error", {}).get("type", "")
