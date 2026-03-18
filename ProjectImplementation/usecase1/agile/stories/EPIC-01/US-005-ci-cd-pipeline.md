# US-005: GitHub Actions CI/CD Pipeline

**Epic:** EPIC-01
**Actor:** `admin`
**Story Points:** 3
**Priority:** High
**Status:** Ready

## User Story

As an **admin**,
I want a CI pipeline that runs on every push to master,
so that linting, type checking, and test failures are caught before they reach the main branch.

## Acceptance Criteria

### AC1: CI pipeline triggers on push and PR
**Given** a developer pushes a commit to any branch or opens a pull request targeting master
**When** GitHub Actions processes the event
**Then** the `ci` workflow runs: checkout → install deps → ruff → mypy → pytest with coverage

### AC2: Failing lint blocks the pipeline
**Given** a commit introduces a ruff linting error
**When** the CI pipeline runs
**Then** the `ruff check` step fails with a non-zero exit code; subsequent steps do not run; the PR is blocked

### AC3: Coverage gate enforced
**Given** a commit reduces test coverage below 80%
**When** the pytest step runs with `--cov=src --cov-fail-under=80`
**Then** the step exits non-zero; the pipeline is marked failed

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] `.github/workflows/ci.yml` committed
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] CI passes on the scaffold with all checks green
- [ ] No hardcoded secrets — use GitHub Actions secrets for any credentials
- [ ] PR squash-merged to master

## Notes

- Use `actions/setup-python@v5` with `python-version: "3.11"`
- Cache pip dependencies with `actions/cache` on `pyproject.toml` hash
- Test PostgreSQL via `services:` with `postgres:16-alpine`; Redis via `services:` with `redis:7-alpine`
