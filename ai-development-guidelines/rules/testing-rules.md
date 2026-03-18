# Testing Rules

> **Comprehensive testing rules are defined in the generic framework file:**
> **[`best-practices_rule_set_code/docs/rules/testing-rules.md`](../../best-practices_rule_set_code/docs/rules/testing-rules.md)**
>
> **Jewelry AI project-specific testing rules extend the generic file:**
> **[`project-specific-guidelines/rules/testing-rules.md`](../../project-specific-guidelines/rules/testing-rules.md)**
>
> **Usecase1 concrete test file locations and per-epic index:**
> **[`ProjectImplementation/usecase1/rules/testing-rules.md`](../../ProjectImplementation/usecase1/rules/testing-rules.md)**

Read those files in order. The following is a quick reference summary.

---

## Quick Reference

### Minimum Coverage: 80%

Enforced by `pytest-cov` in CI. Build fails below 80%.

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

### TDD Workflow (MANDATORY)

1. Write test first (RED — test fails)
2. Run test: verify it fails for the right reason
3. Write minimal implementation (GREEN — test passes)
4. Refactor (IMPROVE)
5. Verify coverage

### Test Types (ALL Required)

- **Unit tests** — every service method, every domain validator; all external dependencies mocked
- **Integration tests** — every API endpoint using `httpx.AsyncClient` + real test DB
- **E2E tests** — full pipeline: upload → match → enrich → outreach

### Test Stack

| Library | Purpose |
|---|---|
| `pytest` + `pytest-asyncio` | Test runner with async support |
| `pytest-cov` | Coverage reporting |
| `pytest-mock` | `mocker` fixture |
| `factory_boy` | Domain object factories |
| `respx` | Mock `httpx` external calls |
| `freezegun` | Freeze time in tests |

### Core Rules

- Never fix a failing test by weakening its assertions — fix the implementation
- Mock external APIs in unit tests; use real test DB in integration tests
- Each test must be independent — no shared mutable state between tests
- Test names must describe the scenario: `test_ingest_lead_raises_on_duplicate_email`
- Use `pytest-asyncio` with `asyncio_mode = "auto"` for all async tests
- All test email addresses must use `@example.com` domains
- Factories used for all domain object construction — never hard-code raw dicts in tests
- No real HTTP calls in CI — mock all external APIs with `respx`

### Fixtures

- Common fixtures in `tests/conftest.py`
- DB fixtures use transaction rollback after each test
- Never seed the production or dev DB from tests
- Use `TEST_DATABASE_URL` environment variable for integration test DB
