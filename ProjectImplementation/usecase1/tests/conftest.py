"""Root test configuration.

Sets required environment variables BEFORE any src imports so that
pydantic-settings can build the Settings object during test collection.

All integration test fixtures live in tests/integration/conftest.py.
All unit test fixtures live in tests/unit/conftest.py.
"""
import os

# ── Test environment variables ────────────────────────────────────────────────
# These must be set before any `from src.xxx import ...` statement.
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("APP_VERSION", "1.0.0-test")
os.environ.setdefault("LOG_LEVEL", "WARNING")  # Suppress info logs during tests
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-chars!")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/jewelry_ai_test",
)
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/jewelry_ai_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("APOLLO_API_KEY", "test-apollo-key")
os.environ.setdefault("HUNTER_API_KEY", "test-hunter-key")
os.environ.setdefault("SENDGRID_API_KEY", "test-sendgrid-key")
os.environ.setdefault("SENDGRID_FROM_EMAIL", "test@example.com")

import pytest

from src.core.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Clear lru_cache before each test so monkeypatch env changes take effect."""
    get_settings.cache_clear()
    yield  # type: ignore[misc]
    get_settings.cache_clear()
