from __future__ import annotations

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core service
    http_host: str = "0.0.0.0"
    http_port: int = int(os.getenv("PORT", "8000"))  # Railway will override this with PORT env var
    default_tz: str = "Australia/Melbourne"
    
    # Environment
    environment: str = "development"  # "development" or "production"

    # Discord
    discord_token: str | None = None

    # Database - Production Supabase PostgreSQL
    database_url: str = "postgresql+asyncpg://postgres:DSCubedAIAgent@db.zqurkolbiilsuqudcyud.supabase.co:5432/postgres"

    # Security
    fernet_key: str | None = None

    # Google OAuth - Configure in Supabase Auth dashboard
    google_client_id: str | None = None
    google_client_secret: str | None = None
    
    # OAuth Configuration - Supabase manages redirect URI
    oauth_state_secret: str = "uEK4I9iIlEQHOlMw0RTw-Pu9Ousrriqdi-AXYkwXsaw"
    google_oauth_scopes: str = "https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/calendar.events"

    # Supabase
    supabase_url: str | None = None
    supabase_key: str | None = None  # Anonymous key for client-side operations
    supabase_service_role_key: str | None = None  # Service role key for backend operations

    # Logging
    log_level: str = "INFO"
    
    @property
    def base_url(self) -> str:
        """Get the base URL for OAuth redirects based on environment"""
        if self.environment == "production":
            # Your actual Railway domain
            return "https://web-production-75e4c.up.railway.app"
        else:
            # Always use localhost for browser access in development
            return f"http://localhost:{self.http_port}"


settings = Settings()


