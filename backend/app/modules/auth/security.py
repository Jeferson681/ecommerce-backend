"""Security utilities for authentication and authorization for Users.

Re-exports from core.security to maintain backward compatibility.
New code should import directly from backend.app.core.security.
"""

from backend.app.core.security import hash_password, verify_password  # noqa: F401

__all__ = ["hash_password", "verify_password"]
