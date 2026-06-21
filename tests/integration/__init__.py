"""Integration tests package."""

import uuid


def unique_email(prefix: str = "user") -> str:
    """Generate a unique email for test isolation."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}@mail.com"
