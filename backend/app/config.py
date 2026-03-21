"""
SelfDiary — Application Configuration.

Environment-based configuration using Pydantic Settings.
All values have safe defaults for local development.


Usage:
    from app.core.config import settings
    print(settings.database_url)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──
    app_name: str = "SelfDiary API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # ── Database ──
    database_url: str = "postgresql+asyncpg://selfdiary:selfdiary_dev@localhost:5432/selfdiary"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # ── JWT (placeholder — implemented in Phase 3) ──
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    # ── S3 / Minio ──
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "selfdiary-attachments"

    # ── Monitoring ──
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1

    # ── CORS ──
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
