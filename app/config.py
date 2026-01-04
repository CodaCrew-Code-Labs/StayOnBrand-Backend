"""
Application configuration using pydantic-settings.
Loads settings from environment variables and .env file.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="StayOnBoard", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment name")

    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])

    # Redis Settings
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: str = Field(default="", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_ssl: bool = Field(default=False, description="Use SSL for Redis")
    redis_cache_ttl: int = Field(default=3600, description="Default cache TTL in seconds")

    # Authentication Settings
    auth_service_url: str = Field(
        default="https://auth.example.com",
        description="External auth service URL",
    )
    auth_service_verify_endpoint: str = Field(
        default="/api/v1/verify",
        description="Auth verification endpoint",
    )
    jwt_secret_key: str = Field(
        default="your-secret-key-here",
        description="JWT secret key for local verification",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_audience: str = Field(default="stayonboard-api", description="JWT audience")

    # File Upload Settings
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    allowed_image_extensions: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp", "svg"],
        description="Allowed image file extensions",
    )
    allowed_mime_types: List[str] = Field(
        default=[
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ],
        description="Allowed MIME types",
    )

    # Storage Settings
    storage_type: str = Field(default="redis", description="Storage backend type")
    storage_prefix: str = Field(default="stayonboard:", description="Storage key prefix")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit requests")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window")

    @field_validator("cors_origins", "allowed_image_extensions", "allowed_mime_types", mode="before")
    @classmethod
    def parse_list(cls, v):
        """Parse string list from environment variable."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [item.strip() for item in v.split(",")]
        return v

    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        protocol = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
