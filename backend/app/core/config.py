from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = Field(default="dev", validation_alias="ENV")
    database_url: str = Field(default="sqlite:///./dev.db", validation_alias="DATABASE_URL")
    cors_origins_raw: Optional[str] = Field(
        default=None,
        validation_alias="CORS_ORIGINS",
    )
    admin_key: str = Field(default="changeme-admin", validation_alias="ADMIN_KEY")
    frontend_public_base: str = Field(
        default="",
        validation_alias="FRONTEND_PUBLIC_BASE",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @staticmethod
    def parse_cors_origins(raw: Optional[str]) -> List[str]:
        if not raw:
            # Default to local frontend for dev
            return ["http://localhost:5173"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    base = Settings()
    # Compute cors_origins property from raw env string.
    cors_list = Settings.parse_cors_origins(base.cors_origins_raw)
    # Pydantic models support model_copy(update=...)
    base = base.model_copy(update={"cors_origins": cors_list})
    return base


