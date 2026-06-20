"""Structured request logging middleware."""

import logging
import time
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class StructuredRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs structured request data after each response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id

        start_time = time.monotonic()

        response: Response = await call_next(request)

        duration_ms = round((time.monotonic() - start_time) * 1000, 1)

        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "level": "INFO",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "request_id": request_id,
        }

        if response.status_code >= 500:
            log_data["level"] = "ERROR"
        elif response.status_code >= 400:
            log_data["level"] = "WARNING"

        logger = logging.getLogger("access")
        logger.info(
            "%s %s %s %sms",
            log_data["method"],
            log_data["path"],
            log_data["status_code"],
            log_data["duration_ms"],
            extra={"http": log_data},
        )

        response.headers["X-Request-ID"] = request_id
        return response
