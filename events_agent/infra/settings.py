from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core service
    http_host: str = "0.0.0.0"
    http_port: int = 8000
    default_tz: str = "Australia/Melbourne"

    # Discord
    discord_token: str | None = None

    # Database
    database_url: str = "sqlite+aiosqlite:///./events_agent.db"

    # Security
    fernet_key: str | None = None

    # Google OAuth
    google_client_id: str | None = None
    google_client_secret: str | None = None
    oauth_redirect_uri: str | None = None

    # Supabase
    supabase_url: str | None = None
    supabase_key: str | None = None

    # Logging
    log_level: str = "INFO"


settings = Settings()


