from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./ecommerce.db"
    APP_NAME: str = "ecommerce-backend"
    DEBUG: bool = True
    # Optional webhook secret for Stripe signatures. Leave empty for local/dev.
    STRIPE_WEBHOOK_SECRET: str | None = None


settings = Settings()
