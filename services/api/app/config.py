from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NEXVARY RealEstate AI OS"
    app_env: str = "development"
    database_url: str = "sqlite:///./nexvary_realestate.db"
    redis_url: str = "redis://localhost:6379/0"
    default_locale: str = "ar"

    jwt_secret: str = "dev-jwt-secret-change-me-please-use-production-secret"
    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = 480
    platform_admin_key: str = "dev-platform-key-change-me"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
