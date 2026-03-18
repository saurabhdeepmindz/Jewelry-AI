# US-002: Project Skeleton and Folder Structure

**Epic:** EPIC-01
**Actor:** `admin`
**Story Points:** 3
**Priority:** Critical
**Status:** Ready

## User Story

As an **admin**,
I want the source code organized in the canonical folder structure defined in Architecture.md,
so that every developer knows exactly where to add new code without asking.

## Acceptance Criteria

### AC1: Full src/ tree created
**Given** the repository is cloned
**When** a developer inspects `src/`
**Then** all directories from Architecture.md exist: `core/`, `db/`, `domain/`, `repositories/`, `services/`, `agents/`, `integrations/`, `tasks/`, `ml/`, `api/`, `ui/`, `scrapers/`; each with an `__init__.py`

### AC2: pyproject.toml is valid and tools are configured
**Given** a developer runs `pip install -e ".[dev]"` in the project root
**When** they run `ruff check src tests` and `mypy src`
**Then** both commands complete with zero errors on the empty scaffold

### AC3: Makefile targets work
**Given** a developer is in the project root with Git Bash or WSL2
**When** they run `make help`
**Then** all defined targets are listed with descriptions; `make check` runs ruff + mypy + pytest and exits 0

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- `pyproject.toml` must configure: `ruff` (line-length=100, target-version=py311), `mypy` (strict=true, python_version=3.11), `pytest` (asyncio_mode=auto, testpaths=["tests"])
- `isort` profile must be `black` to avoid conflict with ruff formatter
