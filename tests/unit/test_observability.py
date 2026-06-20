"""Tests for observability (logging, health checks, correlation ID)."""

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.observability.health.health_check import healthz, readyz

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for /healthz and /readyz endpoints."""

    def test_healthz_returns_200(self) -> None:
        """GET /healthz returns 200 with status ok."""
        resp = client.get("/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    def test_readyz_returns_200_with_db_check(self) -> None:
        """GET /readyz returns 200 with database status."""
        resp = client.get("/readyz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "checks" in body
        assert "database" in body["checks"]
        assert body["checks"]["database"] == "ok"


class TestCorrelationID:
    """Tests for X-Request-ID middleware."""

    def test_correlation_id_generated_when_missing(self) -> None:
        """When no X-Request-ID is sent, one is generated."""
        resp = client.get("/healthz")
        assert resp.status_code == 200
        request_id = resp.headers.get("X-Request-ID")
        assert request_id is not None
        assert len(request_id) > 0

    def test_correlation_id_reused_when_sent(self) -> None:
        """When X-Request-ID is sent, the same value is returned."""
        custom_id = "my-custom-request-id-123"
        resp = client.get("/healthz", headers={"X-Request-ID": custom_id})
        assert resp.status_code == 200
        assert resp.headers.get("X-Request-ID") == custom_id


class TestHealthFunctions:
    """Unit tests for health check functions."""

    def test_healthz_function(self) -> None:
        """healthz() returns basic ok status."""
        result = healthz()
        assert result == {"status": "ok"}

    def test_readyz_function_has_db_check(self) -> None:
        """readyz() returns status with database check."""
        result = readyz()
        assert "status" in result
        assert "checks" in result
        assert "database" in result["checks"]
