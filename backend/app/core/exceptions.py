"""Application-specific exceptions and constants."""


class AppError(Exception):
    """Base class for application-specific exceptions."""

    pass


class Messages:
    """Application-specific messages."""

    INTERNAL_SERVER_ERROR = "An internal server error occurred."

    USER_NOT_FOUND = "User not found."

    EMAIL_ALREADY_EXISTS = "Email already exists."

    EMAIL_OR_PASSWORD_INVALID = "Invalid email or password."  # nosec B105

    PRODUCT_NOT_FOUND = "Product not found."

    INVALID_CREDENTIAL_POLICY = "Credential does not meet the required policy."


class NotFoundError(AppError):
    """Raised when a resource is not found."""

    pass


class InvalidPasswordError(AppError):
    """Raised when password policy validation fails."""

    pass


class ValidationError(AppError):
    """Raised when validation fails."""

    pass


class AuthenticationError(AppError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(AppError):
    """Raised when authorization fails."""

    pass
