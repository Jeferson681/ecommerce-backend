"""Security utilities shared across modules.

Provides password hashing, password verification and password policy
validation. Authorization logic (admin checks) belongs to the User domain.
"""

import bcrypt

# Characters considered "special" for password policy validation
SPECIAL_CHARACTERS = "!@#$%^&*()-+"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def validate_password_policy(password: str) -> bool:
    """Validate password against the security policy.

    Requires at least one uppercase letter, one lowercase letter,
    one digit, and one special character.
    """
    has_uppercase = any(c.isupper() for c in password)
    has_lowercase = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in SPECIAL_CHARACTERS for c in password)

    return all([has_uppercase, has_lowercase, has_digit, has_special])
