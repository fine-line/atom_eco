from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App info
    version: str
    docs_url: str
    # Admin settings
    admin_email: str
    admin_password: str
    # JWT settings
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30
    # Load from .env
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()
