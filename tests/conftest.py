from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path


def _sqlite_temp_db_url() -> str:
    # Use a per-run file DB to avoid cross-test contamination and keep
    # engine creation simple (no special in-memory pooling requirements).
    db_path = Path(tempfile.gettempdir()) / f"ecommerce_test_{uuid.uuid4().hex}.db"
    return f"sqlite:///{db_path.as_posix()}"


# Ensure tests never touch the developer Postgres DB by default.
os.environ.setdefault("DATABASE_URL", _sqlite_temp_db_url())
