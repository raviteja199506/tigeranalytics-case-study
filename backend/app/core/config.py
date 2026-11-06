from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRICING_", env_file=".env", extra="ignore")

    app_name: str = "Pricing Feed Service"
    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./pricing.db"
    database_pool_size: int = Field(default=10, ge=1)
    database_max_overflow: int = Field(default=20, ge=0)

    storage_dir: Path = Path("./data/uploads")
    max_upload_bytes: int = Field(default=512 * 1024 * 1024, ge=1)
    ingestion_batch_size: int = Field(default=5_000, ge=100, le=50_000)
    max_reported_errors: int = Field(default=1_000, ge=0)

    cors_origins: list[str] = ["http://localhost:5173"]

    auth_mode: Literal["disabled", "jwt"] = "disabled"
    jwt_jwks_url: str | None = None
    jwt_audience: str | None = None
    jwt_issuer: str | None = None
    jwt_roles_claim: str = "roles"

    @model_validator(mode="after")
    def validate_security(self) -> Self:
        if self.auth_mode == "jwt" and not self.jwt_jwks_url:
            raise ValueError("PRICING_JWT_JWKS_URL is required when auth_mode is 'jwt'")
        if self.environment == "production" and self.auth_mode == "disabled":
            raise ValueError("Authentication cannot be disabled in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
