"""Backend settings (env-driven)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://gridlock:gridlock@localhost:5432/gridlock"
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

    # Notifications
    notification_mode: str = "console"  # 'console' or 'live'
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    twilio_sid: str = ""
    twilio_token: str = ""
    twilio_from: str = ""

    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
