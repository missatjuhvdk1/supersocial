from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings using Pydantic Settings."""

    # API Settings
    app_name: str = "TikTok Auto-Poster"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Database Settings
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/tiktok_autoposter"

    # Redis Settings
    redis_url: str = "redis://localhost:6379/0"

    # Celery Settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # File Upload Settings
    max_upload_size: int = 500 * 1024 * 1024  # 500 MB
    upload_dir: str = "./uploads"

    # TikTok Settings
    tiktok_upload_timeout: int = 300  # seconds
    tiktok_headless: bool = True
    max_concurrent_uploads: int = 5

    # Browser Settings
    headless_browser: bool = True
    browser_timeout: int = 60

    # External APIs
    sadcaptcha_api_key: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra env vars not defined here
    )


settings = Settings()
