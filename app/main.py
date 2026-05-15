from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers.auth import router as auth_router
from app.api.routers.product import router as product_router
from app.api.routers.user import router as user_router
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Ensure database tables exist for tests/local runs
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ecommerce-backend", lifespan=lifespan)

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(product_router)

    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.add_api_route("/healthz", healthz, methods=["GET"])

    return app


app = create_app()
