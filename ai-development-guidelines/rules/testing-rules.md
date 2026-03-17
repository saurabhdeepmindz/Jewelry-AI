# Testing Rules

## Minimum Coverage: 80%

Enforced by `pytest-cov` in CI. Build fails below 80%.

## TDD Workflow (MANDATORY)

1. Write test first (RED — test fails)
2. Run test: verify it fails for the right reason
3. Write minimal implementation (GREEN — test passes)
4. Refactor (IMPROVE)
5. Verify coverage

## Test Types (ALL Required)

- **Unit tests** — every service method, every domain validator
- **Integration tests** — every API endpoint using `httpx.AsyncClient`
- **E2E tests** — full pipeline: upload → match → enrich → outreach

## Test Organization

```
tests/
├── unit/
│   ├── services/
│   ├── domain/
│   └── agents/
├── integration/
│   └── api/
└── e2e/
    └── pipeline/
```

## Rules

- Never fix a failing test by weakening its assertions — fix the implementation
- Mock external APIs in unit tests; use real DB in integration tests
- Each test must be independent — no shared mutable state between tests
- Test names must describe the scenario: `test_ingest_lead_raises_on_duplicate_email`
- Use `pytest-asyncio` for all async tests

## Fixtures

- Common fixtures in `tests/conftest.py`
- DB fixtures use transactions that are rolled back after each test
- Never seed the production/dev DB from tests
