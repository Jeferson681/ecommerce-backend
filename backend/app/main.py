import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routers.admin import router as admin_router
from backend.app.api.routers.auth import router as auth_router
from backend.app.api.routers.cart import router as cart_router
from backend.app.api.routers.order import router as order_router
from backend.app.api.routers.payment import router as payment_router
from backend.app.api.routers.payment_webhook import router as payment_webhook_router
from backend.app.api.routers.product import router as product_router
from backend.app.api.routers.user import router as user_router
from backend.app.core.config import settings
from backend.app.core.database import Base, engine
from backend.app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    Messages,
    NotFoundError,
    ValidationError,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Ensure database tables exist for tests/local runs
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ecommerce-backend", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(cart_router)
    app.include_router(order_router)
    app.include_router(payment_router)
    app.include_router(payment_webhook_router)
    app.include_router(user_router)
    app.include_router(product_router)

    # Structured handler for known application errors
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        status_code = 400
        if isinstance(exc, NotFoundError):
            status_code = 404
        elif isinstance(exc, AuthenticationError):
            status_code = 401
        elif isinstance(exc, AuthorizationError):
            status_code = 403
        elif isinstance(exc, ValidationError):
            status_code = 400

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc) or Messages.INTERNAL_SERVER_ERROR,
                }
            },
        )

    # General handler that reveals details only in DEBUG mode
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        if settings.DEBUG:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                        "trace": traceback.format_exc(),
                    }
                },
            )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": Messages.INTERNAL_SERVER_ERROR,
                }
            },
        )

    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.add_api_route("/healthz", healthz, methods=["GET"])

    return app


app = create_app()
