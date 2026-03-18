"""Application configuration using pydantic-settings.

All environment variables are read from .env file and validated at startup.
Missing required variables raise ValidationError before the app starts.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. All required fields have no default value — missing → startup fail."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "development"   # development | staging | production | testing
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str                # REQUIRED — no default

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str              # REQUIRED — postgresql+asyncpg://...
    TEST_DATABASE_URL: str = ""   # Optional — used by integration tests

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── External APIs ─────────────────────────────────────────────────────────
    OPENAI_API_KEY: str            # REQUIRED
    ANTHROPIC_API_KEY: str = ""
    APOLLO_API_KEY: str            # REQUIRED
    HUNTER_API_KEY: str            # REQUIRED
    PROXYCURL_API_KEY: str = ""
    SENDGRID_API_KEY: str          # REQUIRED
    SENDGRID_FROM_EMAIL: str       # REQUIRED
    SENDGRID_WEBHOOK_SECRET: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""
    N8N_WEBHOOK_URL: str = ""
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    # ── Feature flags ─────────────────────────────────────────────────────────
    HUMAN_REVIEW_REQUIRED: bool = True
    MAX_BATCH_SIZE: int = 500
    ENRICHMENT_CACHE_TTL_DAYS: int = 7
    INVENTORY_MATCH_MIN_CARAT: float = 0.50
    LEAD_SCORE_HIGH_THRESHOLD: float = 70.0
    LEAD_SCORE_LOW_THRESHOLD: float = 40.0

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REP: str = "100/minute"
    RATE_LIMIT_MANAGER: str = "300/minute"


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance. Call get_settings.cache_clear() in tests."""
    return Settings()
