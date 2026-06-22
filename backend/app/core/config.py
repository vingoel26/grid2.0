"""Backend settings (env-driven)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./gridlock.db"
    redis_url: str = "redis://localhost:6379"

    ml_api_key: str = "gridlock-ml-key-change-me"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "gridlock"
    minio_secret_key: str = "gridlock123"
    minio_bucket: str = "evidence"
    minio_secure: bool = False

    cors_origins: list[str] = ["http://localhost:3000"]

    mappls_api_key: str | None = None


settings = Settings()
