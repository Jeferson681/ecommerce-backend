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
    DEBUG: bool = True
    # Optional webhook secret for Stripe signatures. Leave empty for local/dev.
    STRIPE_WEBHOOK_SECRET: str | None = None
    # Stripe API keys for real payment processing in test mode.
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None


settings = Settings()
