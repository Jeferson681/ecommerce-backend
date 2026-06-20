"""Health check endpoints for liveness and readiness probes."""

from sqlalchemy import text

from backend.app.core.database import SessionLocal


def healthz() -> dict[str, str]:
    """Liveness probe — lightweight check that the app is running."""
    return {"status": "ok"}


def readyz() -> dict:
    """Readiness probe — checks database connectivity."""
    db_status: str = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:
        db_status = f"error: {exc}"

    overall = "ok" if db_status == "ok" else "degraded"
    return {
        "status": overall,
        "checks": {
            "database": db_status,
        },
    }
