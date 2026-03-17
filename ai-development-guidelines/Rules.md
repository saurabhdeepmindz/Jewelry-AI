# Rules — Jewelry AI Platform

This is the **master rules file**. It provides references to all specialized rules files that govern development on this project. All contributors and AI agents MUST follow these rules.

---

## Quick Reference

| Rule Area | File | Summary |
|---|---|---|
| Coding Style | [rules/coding-style-rules.md](rules/coding-style-rules.md) | Immutability, naming, file size, nesting |
| Security | [rules/security-rules.md](rules/security-rules.md) | Secrets, input validation, auth |
| Testing | [rules/testing-rules.md](rules/testing-rules.md) | TDD, 80% coverage, test types |
| API Design | [rules/api-design-rules.md](rules/api-design-rules.md) | REST conventions, error format |
| Data | [rules/data-rules.md](rules/data-rules.md) | Database, migrations, soft deletes |

---

## Non-Negotiable Rules (Always Apply)

1. **No secrets in code** — API keys, passwords, tokens go in `.env` only. See [security-rules.md](rules/security-rules.md).
2. **No mutation of domain objects** — Always return new objects. See [coding-style-rules.md](rules/coding-style-rules.md).
3. **Tests before implementation** — Write the test first. See [testing-rules.md](rules/testing-rules.md).
4. **Full docstrings on all public methods** — See [CodingStandards.md](CodingStandards.md).
5. **Validate at all system boundaries** — User input, API responses, file content. See [security-rules.md](rules/security-rules.md).
6. **Structured logging with context** — Every log MUST include trace_id and entity ID. See [Architecture.md](Architecture.md).
7. **Handle all exceptions explicitly** — Never swallow errors silently. See [Architecture.md](Architecture.md).
8. **Use async for all I/O** — No blocking calls on the event loop. See [coding-style-rules.md](rules/coding-style-rules.md).

---

## Design Principles

- **Separation of Concerns** — Each class/module has one responsibility.
- **Dependency Injection** — Services receive dependencies; they don't create them.
- **Repository Pattern** — All DB access behind repository interfaces.
- **Strategy Pattern** — Pluggable algorithms (enrichment providers, scoring).
- **Event-Driven** — Services communicate via events, not direct calls where possible.

For full pattern details see [DesignPatterns.md](DesignPatterns.md).

---

## Technology Constraints

- Python 3.11+ only
- FastAPI for all API endpoints (no Flask, no Django)
- SQLAlchemy 2.x async only (no sync ORM calls)
- LangChain / LangGraph for all AI orchestration (no raw OpenAI calls in services)
- All background jobs via Celery (no `asyncio.create_task` for fire-and-forget)
- All config via `pydantic-settings` (no `os.environ.get()` directly in services)
