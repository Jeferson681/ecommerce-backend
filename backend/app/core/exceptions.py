"""Application-specific exceptions and constants."""


class AppError(Exception):
    """Base class for application-specific exceptions."""

    pass


class Messages:
    """Application-specific messages."""

    INTERNAL_SERVER_ERROR = "An internal server error occurred."

    USER_NOT_FOUND = "User not found."

    INVALID_PAYMENT_STATUS = "Invalid payment status."

    EMAIL_ALREADY_EXISTS = "Email already exists."

    EMAIL_OR_PASSWORD_INVALID = "Invalid email or password."  # nosec B105

    PRODUCT_NOT_FOUND = "Product not found."

    CART_NOT_FOUND = "Cart not found."

    CART_ITEM_NOT_FOUND = "Cart item not found."

    ORDER_NOT_FOUND = "Order not found."
    PAYMENT_NOT_FOUND = "Payment not found."
    PAYMENT_AMOUNT_MISMATCH = "Payment amount does not match order total."
    ORDER_CART_EMPTY = "Cart is empty. Add items before checkout."
    ORDER_INSUFFICIENT_STOCK = "Insufficient stock for product."

    INVALID_CREDENTIAL_POLICY = "Credential does not meet the required policy."

    NO_FAILED_PAYMENT_FOUND = "No failed payment found for the order."

    ORDER_IS_NOT_PENDING = "Order is not in the pending status."


class NotFoundError(AppError):
    """Raised when a resource is not found."""

    pass


class InvalidPasswordError(AppError):
    """Raised when password policy validation fails."""

    pass


class ValidationError(AppError):
    """Raised when validation fails."""

    pass


class ConflictError(AppError):
    """Raised when a persistence operation conflicts with existing data."""

    pass


class AuthenticationError(AppError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(AppError):
    """Raised when authorization fails."""

    pass


class EmailAlreadyExistsError(AppError):
    """Raised when a user with the given email already exists."""

    pass
