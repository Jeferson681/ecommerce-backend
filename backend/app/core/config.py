from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./ecommerce.db"
    APP_NAME: str = "ecommerce-backend"
    DEBUG: bool = True


settings = Settings()
