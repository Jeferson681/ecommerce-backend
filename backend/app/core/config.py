from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'ecommerce.db'}"
    APP_NAME: str = "ecommerce-backend"
    DEBUG: bool = True
    # Optional webhook secret for Stripe signatures. Leave empty for local/dev.
    STRIPE_WEBHOOK_SECRET: str | None = None


settings = Settings()
