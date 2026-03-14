"""
SelfDiary — Application Configuration.

Reads environment variables via Pydantic Settings.
All config values have safe defaults for local development.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── General ──
    environment: str = "development"
    debug: bool = False

    # ── Database ──
    database_url: str = "postgresql+asyncpg://selfdiary:selfdiary_dev@localhost:5432/selfdiary"

    # ── JWT ──
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    # ── S3 / Minio ──
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "selfdiary-attachments"

    # ── CORS ──
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
