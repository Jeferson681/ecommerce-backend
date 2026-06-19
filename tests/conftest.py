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


# Integration tests run by default. The session fixture below creates and
# drops the temporary test schema used by integration tests.


@pytest.fixture(scope="session", autouse=True)
def _create_test_schema() -> None:
    """Create the default test schema once for integration tests.

    The schema is created at session start and dropped at the end. This
    fixture always runs so integration tests don't require additional env
    variables to be enabled.
    """
    # Import modules that register ORM models so they are present in metadata.
    # This avoids NoReferencedTableError when creating the schema.
    import backend.app.idempotency.domain.models  # noqa: F401
    import backend.app.modules.auth.domain.models  # noqa: F401
    import backend.app.modules.cart.domain.models  # noqa: F401
    import backend.app.modules.order.domain.models  # noqa: F401
    import backend.app.modules.payment.domain.models  # noqa: F401
    import backend.app.modules.product.domain.models  # noqa: F401
    import backend.app.modules.user.domain.models  # noqa: F401
    from backend.app.core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)
