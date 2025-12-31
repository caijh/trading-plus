from pydantic_settings import BaseSettings

from app.core.env import DATABASE_URL


class Settings(BaseSettings):
    sqlalchemy_string: str = DATABASE_URL


settings = Settings()
