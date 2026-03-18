# EPIC-01: Platform Foundation & Infrastructure

**Status:** Ready
**Phase:** Phase 0
**Layer(s):** All layers (prerequisite)
**Priority:** Critical
**Estimated Size:** L

---

## Problem Statement

Before any business logic can be built, the platform needs a working local development environment, a clean project scaffold, validated configuration management, a database connection layer, and a baseline CI/CD pipeline. Without this foundation, every subsequent epic is blocked.

## Goal

A developer can clone the repository, run `make up`, and have all services running locally (FastAPI, PostgreSQL, Redis, Celery) with all Alembic migrations applied, all linting and type checks passing, and a CI pipeline executing on every push to master.

## Scope (In)

- Docker Compose with all services: FastAPI, PostgreSQL 16, Redis 7, Celery worker
- Project scaffold: full `src/` folder structure per Architecture.md
- `pyproject.toml` with ruff, mypy, pytest, isort configuration
- `.gitattributes` for cross-platform line ending enforcement
- Pydantic-settings `Settings` class with startup validation
- Async SQLAlchemy engine + `get_async_session()` dependency
- Alembic baseline migration (001) + schema migrations (002–007)
- FastAPI app entrypoint with lifespan, CORS, global exception handler
- Makefile with standard developer commands
- GitHub Actions CI workflow (lint + type check + test)
- `.env.example` committed; `.env` in `.gitignore`

## Scope (Out)

- Authentication / JWT (EPIC-11)
- Any domain business logic (EPIC-02 onward)
- Production deployment / Kubernetes (EPIC-14)
- Monitoring stack / Prometheus (EPIC-15)

---

## Acceptance Criteria

- [ ] AC1: `make up` starts all containers with no errors; FastAPI `/health` returns 200
- [ ] AC2: `make migrate` applies all migrations to a fresh PostgreSQL instance without errors
- [ ] AC3: `make check` (ruff + mypy + pytest) passes with zero errors on a clean checkout
- [ ] AC4: `.env.example` documents every required environment variable
- [ ] AC5: GitHub Actions CI triggers on push to master and runs all checks

---

## User Stories

- US-001: Dev environment and Docker Compose setup — `agile/stories/EPIC-01/US-001-dev-environment-setup.md`
- US-002: Project skeleton and folder structure — `agile/stories/EPIC-01/US-002-project-skeleton.md`
- US-003: Pydantic-settings configuration with startup validation — `agile/stories/EPIC-01/US-003-configuration-setup.md`
- US-004: Alembic baseline and schema migrations — `agile/stories/EPIC-01/US-004-alembic-migrations.md`
- US-005: GitHub Actions CI/CD pipeline — `agile/stories/EPIC-01/US-005-ci-cd-pipeline.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| None | This epic has no external API dependencies | — |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Alembic migrations applied cleanly on a fresh DB
- [ ] API `/health` endpoint documented in OpenAPI
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
