from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    api_repository_backend: str = "static"
    database_url: str | None = None
    data_dir: Path = Field(default=Path("data"))
    model_dir: Path = Field(default=Path("artifacts/models"))
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if not isinstance(value, str) or not value:
            return value
        normalized = value
        if normalized.startswith("postgres://"):
            normalized = normalized.replace("postgres://", "postgresql+asyncpg://", 1)
        elif normalized.startswith("postgresql://"):
            normalized = normalized.replace("postgresql://", "postgresql+asyncpg://", 1)

        parts = urlsplit(normalized)
        query_params = parse_qsl(parts.query, keep_blank_values=True)
        translated_params: list[tuple[str, str]] = []
        for key, param_value in query_params:
            if key == "sslmode":
                translated_params.append(("ssl", "require" if param_value else "true"))
            else:
                translated_params.append((key, param_value))

        normalized_query = urlencode(translated_params)
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, normalized_query, parts.fragment)
        )

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def normalize_cors_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
