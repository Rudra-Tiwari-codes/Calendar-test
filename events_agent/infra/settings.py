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

    # Database - Production Supabase PostgreSQL
    database_url: str = "postgresql+asyncpg://postgres:DSCubedAIAgent@db.zqurkolbiilsuqudcyud.supabase.co:5432/postgres"

    # Security
    fernet_key: str | None = None

    # Google OAuth - Managed by Supabase
    google_client_id: str | None = None
    google_client_secret: str | None = None
    
    # OAuth Configuration
    oauth_redirect_uri: str = "https://zqurkolbiilsuqudcyud.supabase.co/auth/v1/callback"
    oauth_state_secret: str = "uEK4I9iIlEQHOlMw0RTw-Pu9Ousrriqdi-AXYkwXsaw"
    google_oauth_scopes: str = "https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/calendar.events"

    # Supabase
    supabase_url: str | None = None
    supabase_key: str | None = None

    # Logging
    log_level: str = "INFO"


settings = Settings()


