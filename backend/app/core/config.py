from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'ecommerce.db'}"
    APP_NAME: str = "ecommerce-backend"
    DEBUG: bool = False

    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None

    JWT_SECRET_KEY: str
    JWT_ISSUER: str = "ecommerce-backend"
    JWT_AUDIENCE: str = "ecommerce-frontend"

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
