from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NEXVARY RealEstate AI OS"
    app_env: str = "development"
    database_url: str = "sqlite:///./nexvary_realestate.db"
    redis_url: str = "redis://localhost:6379/0"
    default_locale: str = "ar"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
