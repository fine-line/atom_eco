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

    # db service name
    db_service: str
    # db credentials
    db_user: str
    db_password: str

    # Fake db service name
    fake_db_service: str
    # Fake db credentials
    fake_db_user: str
    fake_db_password: str

    # Load from .env
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()
