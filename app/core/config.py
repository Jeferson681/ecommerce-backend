from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/ecommerce"
    )
    APP_NAME: str = "ecommerce-backend"
    DEBUG: bool = True


settings = Settings()
