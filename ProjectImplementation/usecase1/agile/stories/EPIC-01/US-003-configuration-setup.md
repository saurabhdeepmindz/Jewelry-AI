# US-003: Pydantic-Settings Configuration with Startup Validation

**Epic:** EPIC-01
**Actor:** `system`
**Story Points:** 3
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want all configuration loaded from environment variables at startup with validation,
so that missing or invalid settings are caught immediately — not silently at runtime.

## Acceptance Criteria

### AC1: Missing required setting crashes on startup
**Given** the `.env` file is missing `DATABASE_URL`
**When** the FastAPI application starts
**Then** it raises `pydantic_settings.ValidationError` with a clear message naming the missing field; the process exits non-zero

### AC2: Invalid setting value crashes on startup
**Given** `DATABASE_URL` is set to `postgresql://...` (wrong driver — must be `postgresql+asyncpg://`)
**When** the FastAPI application starts
**Then** a `ValidationError` is raised with message: "DATABASE_URL must use asyncpg driver"

### AC3: All settings accessible via singleton
**Given** the application is running normally
**When** any module calls `from src.core.config import get_settings; s = get_settings()`
**Then** it returns the same `Settings` instance (singleton via `lru_cache`) with all fields populated

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: app starts cleanly with valid `.env`
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Feature flags must have safe defaults: `HUMAN_REVIEW_REQUIRED=True`, `ENRICHMENT_ENABLED=True`
- `DB_ECHO=False` by default; set `True` in dev via `.env` for SQL logging
- `get_settings()` uses `@lru_cache(maxsize=1)` — never instantiate `Settings()` directly elsewhere
