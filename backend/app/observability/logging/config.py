"""Centralized logging configuration using Python's native logging module.

Provides a consistent formatter and level configuration for all application
loggers. Avoids duplicate handlers by clearing existing handlers on the root
logger before configuring.
"""

import logging
import sys

# Default log format with timestamp, level, logger name, and message.
# Includes request_id when present via the `extra` parameter.
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class RequestIdFilter(logging.Filter):
    """Adds request_id to log records when available in the extra context."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", "-")
        return True


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a consistent formatter and handler.

    Args:
        level: Logging level for the root logger. Defaults to INFO.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicate log lines.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root.addHandler(handler)

    # Ensure the "access" logger used by the request middleware is configured.
    access_logger = logging.getLogger("access")
    access_logger.setLevel(level)
    access_logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the request_id filter applied.

    Args:
        name: Logger name, typically __name__.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    # Add filter only if not already present to avoid duplicates.
    if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
        logger.addFilter(RequestIdFilter())
    return logger
