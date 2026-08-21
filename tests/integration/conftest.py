"""Pytest configuration for integration tests.

Automatically applies the ``integration`` marker to every test collected
from the ``tests/integration`` directory. This guarantees the CI workflows
that run ``-m integration`` and ``-m "not integration"`` correctly separate
unit and integration tests without requiring per-file markers.
"""

from pathlib import Path

import pytest


def pytest_collection_modifyitems(config, items):
    """Apply the ``integration`` marker to all tests in this directory."""
    integration_dir = Path(__file__).parent.resolve()
    for item in items:
        # Only mark tests that actually live under tests/integration.
        if integration_dir in Path(str(item.fspath)).resolve().parents:
            if item.get_closest_marker("integration") is None:
                item.add_marker(pytest.mark.integration)
