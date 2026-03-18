# US-004: Alembic Baseline and Schema Migrations

**Epic:** EPIC-01
**Actor:** `system`
**Story Points:** 5
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want all database schema changes managed through Alembic migrations,
so that any developer can reproduce the exact production schema on a fresh database with one command.

## Acceptance Criteria

### AC1: Fresh database migrated cleanly
**Given** a fresh PostgreSQL instance with no tables
**When** `alembic upgrade head` is run
**Then** all 7 migrations apply in order (001–007) with no errors; all tables and indexes from DB_SCHEMA.md exist

### AC2: pgvector extension enabled
**Given** migration 007 has been applied
**When** `SELECT * FROM pg_extension WHERE extname = 'vector'` is run
**Then** one row is returned confirming pgvector is active; `leads.embedding VECTOR(1536)` column exists

### AC3: Migration downgrade works for last migration
**Given** all migrations are applied
**When** `alembic downgrade -1` is run
**Then** migration 007 is reversed cleanly; `leads.embedding` column no longer exists; `alembic upgrade head` re-applies it

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Integration test: fresh DB → `alembic upgrade head` → all tables present
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Migration 001 is an empty baseline — establishes the `alembic_version` table only
- Migration naming: `NNN_verb_noun.py` — e.g., `002_create_leads_inventory.py`
- `env.py` must use async SQLAlchemy engine: `run_async_migrations()` pattern
- `alembic.ini` must read `DATABASE_URL` from environment (not hardcoded)
