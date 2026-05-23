from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest


def _sqlite_temp_db_url() -> str:
    # Use a per-run file DB to avoid cross-test contamination and keep
    # engine creation simple (no special in-memory pooling requirements).
    db_path = Path(tempfile.gettempdir()) / f"ecommerce_test_{uuid.uuid4().hex}.db"
    return f"sqlite:///{db_path.as_posix()}"


# Ensure tests never touch the developer Postgres DB by default.
os.environ.setdefault("DATABASE_URL", _sqlite_temp_db_url())


# By default, integration tests are considered CI-only. Locally they are skipped
# unless one of the environment variables below is set. This prevents slow or
# infra-dependent tests from running in a developer environment.
def pytest_collection_modifyitems(config, items):
    run_integration = bool(os.getenv("CI") or os.getenv("RUN_INTEGRATION_TESTS"))

    if not run_integration:
        skip_integration = pytest.mark.skip(
            reason=(
                "Integration tests skipped locally. Set CI=true or "
                "RUN_INTEGRATION_TESTS=1 to enable them."
            )
        )
        for item in items:
            # tests marked with @pytest.mark.integration
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


@pytest.fixture(scope="session", autouse=True)
def _create_test_schema() -> None:
    """Create the default test schema once when integration tests run."""
    run_integration = bool(os.getenv("CI") or os.getenv("RUN_INTEGRATION_TESTS"))

    if not run_integration:
        yield
        return

    from backend.app.core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)
