"""Password validation functions."""

SPECIAL_CHARACTERS = "!@#$%^&*()-+"


def validate_password_policy(password: str) -> bool:
    """Validate the password against the policy.
    To check for one uppercase letter, one lowercase letter, one number, one special character, and a minimum length of 8.
    """

    has_uppercase = any(c.isupper() for c in password)
    has_lowercase = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in SPECIAL_CHARACTERS for c in password)

    return all(
        [
            has_uppercase,
            has_lowercase,
            has_digit,
            has_special,
        ]
    )
