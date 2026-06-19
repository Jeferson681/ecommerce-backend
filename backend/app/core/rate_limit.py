"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request, exc: RateLimitExceeded):
    """Return 429 JSON response when rate limit is exceeded."""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "type": "RateLimitExceeded",
                "message": "Too many requests. Please try again later.",
            }
        },
    )
