"""Unit tests for src/core/config.py — US-003.

TDD: These tests define the expected behaviour of Settings.
Run: pytest tests/unit/core/test_config.py -v
"""
import pytest
from pydantic import ValidationError


class TestSettings:
    """Settings must load correctly and fail fast on missing required vars."""

    def test_settings_loads_required_fields_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given all required env vars → Settings populates all fields."""
        monkeypatch.setenv("SECRET_KEY", "my-test-secret-32-chars-minimum!!")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host/db")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
        monkeypatch.setenv("APOLLO_API_KEY", "apollo-key")
        monkeypatch.setenv("HUNTER_API_KEY", "hunter-key")
        monkeypatch.setenv("SENDGRID_API_KEY", "sg-key")
        monkeypatch.setenv("SENDGRID_FROM_EMAIL", "from@example.com")

        from src.core.config import Settings
        s = Settings()

        assert s.SECRET_KEY == "my-test-secret-32-chars-minimum!!"
        assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@host/db"
        assert s.OPENAI_API_KEY == "sk-test-openai"

    def test_settings_raises_on_missing_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given DATABASE_URL is absent → Settings raises ValidationError at startup."""
        monkeypatch.delenv("DATABASE_URL", raising=False)

        from src.core.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "DATABASE_URL" in str(exc_info.value)

    def test_settings_raises_on_missing_secret_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given SECRET_KEY is absent → Settings raises ValidationError."""
        monkeypatch.delenv("SECRET_KEY", raising=False)

        from src.core.config import Settings
        with pytest.raises(ValidationError):
            Settings()

    def test_human_review_required_defaults_to_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default value for HUMAN_REVIEW_REQUIRED must be True (safety default)."""
        monkeypatch.delenv("HUMAN_REVIEW_REQUIRED", raising=False)

        from src.core.config import Settings
        s = Settings()

        assert s.HUMAN_REVIEW_REQUIRED is True

    def test_human_review_can_be_disabled_for_testing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Setting HUMAN_REVIEW_REQUIRED=false overrides the default."""
        monkeypatch.setenv("HUMAN_REVIEW_REQUIRED", "false")

        from src.core.config import Settings
        s = Settings()

        assert s.HUMAN_REVIEW_REQUIRED is False

    def test_app_version_has_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """APP_VERSION defaults to 1.0.0 when not set."""
        monkeypatch.delenv("APP_VERSION", raising=False)

        from src.core.config import Settings
        s = Settings()

        assert s.APP_VERSION == "1.0.0"

    def test_get_settings_returns_same_instance(self) -> None:
        """get_settings() is cached — same object returned on repeated calls."""
        from src.core.config import get_settings

        s1 = get_settings()
        s2 = get_settings()

        assert s1 is s2

    def test_optional_fields_default_to_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Optional API keys default to empty string when not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("PROXYCURL_API_KEY", raising=False)
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)

        from src.core.config import Settings
        s = Settings()

        assert s.ANTHROPIC_API_KEY == ""
        assert s.PROXYCURL_API_KEY == ""
        assert s.TWILIO_ACCOUNT_SID == ""
