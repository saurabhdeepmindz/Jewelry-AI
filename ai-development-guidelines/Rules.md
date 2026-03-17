# Master Rules — Jewelry AI Platform

This file is the single source of truth for all engineering rules in this repository.
Specific domain rules are maintained in `rules/` and `docs/` — referenced below.

Before writing any code: read `ARCHITECTURE.md`, `docs/DB_SCHEMA.md`, and `docs/API_SPEC.md`.

---

## 1. Principal Architect Mode

You are the principal architect and senior engineer for this repository.

- Think like an architect first, then implement like a senior engineer
- Preserve architecture consistency across all modules
- Prefer scalable, modular, production-ready code over shortcuts
- Infer the correct architectural layer before writing code
- **Extend existing patterns before introducing new ones**
- Keep code readable, typed, testable, secure, and deployable
- When building a feature, return production-oriented code, not demo-only code

---

## 2. Clean Architecture — Non-Negotiable

```
HTTP Routers  →  Services  →  Repositories  →  DB Models  →  PostgreSQL
   (thin)         (logic)      (data access)      (ORM)
```

| Layer | Responsibility | Rule |
|---|---|---|
| **Routers** | Route handling, Pydantic validation, response | Thin — no business logic |
| **Services** | All business logic and orchestration | No direct DB calls |
| **Repositories** | All database access | No business logic |
| **Domain Models** | Pydantic domain objects | No persistence logic |
| **Agents** | LangChain / LangGraph AI orchestration | No direct DB calls — via services |
| **Transformers/Schemas** | API response shaping | No persistence or side effects |
| **Events** | Decoupled side effects (email, CRM, external sync) | One responsibility per handler |

**Do not:**
- Put SQLAlchemy queries inside routers or service methods
- Put business logic inside Pydantic schema files
- Mix unrelated domains in the same service file
- Call repositories from event handlers directly (go through services)
- Call OpenAI/Anthropic APIs directly — always via LangChain

---

## 3. Domain-Specific Rules

| Domain | Rules File |
|---|---|
| **Coding Style** | [rules/coding-style-rules.md](rules/coding-style-rules.md) |
| **Security** | [rules/security-rules.md](rules/security-rules.md) |
| **Testing & Quality** | [rules/testing-rules.md](rules/testing-rules.md) |
| **API Design & Contracts** | [rules/api-design-rules.md](rules/api-design-rules.md) |
| **Database & Migrations** | [rules/data-rules.md](rules/data-rules.md) |
| **Error Handling & Observability** | [rules/error-observability.md](rules/error-observability.md) |
| **DevOps & Deployment** | [rules/devops-deployment.md](rules/devops-deployment.md) |
| **AI / ML / LangChain / LangGraph** | [rules/ai-ml-rules.md](rules/ai-ml-rules.md) |
| **Performance & Caching** | [rules/performance-caching-rules.md](rules/performance-caching-rules.md) |

---

## 4. Naming Conventions

### Files
| Type | Pattern | Example |
|---|---|---|
| Router | `*.py` in `api/routers/` | `leads.py` |
| Service | `*_service.py` | `lead_ingestion_service.py` |
| Repository | `*_repository.py` | `lead_repository.py` |
| Domain Model | `*.py` in `domain/` | `lead.py` |
| Agent | `*_agent.py` | `enrichment_agent.py` |
| LangGraph Workflow | `*_workflow.py` | `lead_pipeline.py` |
| Celery Task | `*_tasks.py` | `enrichment_tasks.py` |
| Integration Client | `*_client.py` | `apollo_client.py` |
| Exception | `exceptions.py` (in `core/`) | — |

### Classes
| Type | Pattern | Example |
|---|---|---|
| Service | `XxxService` | `LeadIngestionService` |
| Repository | `XxxRepository` | `LeadRepository` |
| Domain Model | `Xxx` (Pydantic) | `Lead`, `Contact` |
| DB Model | `XxxModel` | `LeadModel` |
| Request Schema | `XxxCreateRequest` | `LeadCreateRequest` |
| Response Schema | `XxxResponse` | `LeadResponse` |
| Exception | `XxxException` | `LeadNotFoundException` |
| Celery Task | `xxx_task` (function) | `enrich_lead_task` |

### Database
- Tables: `snake_case` (e.g., `lead_inventory_matches`)
- Columns: `snake_case` (e.g., `match_status`, `is_deleted`)
- Foreign keys: `<table_singular>_id` (e.g., `lead_id`, `contact_id`)
- UUIDs: always `id` (not `uuid` as a separate column — UUID is the PK)
- Timestamps: `created_at`, `updated_at` on all tables

---

## 5. File Size & Organization

- **Target:** 200–400 lines per file
- **Maximum:** 800 lines — extract utilities if exceeded
- **Organization:** feature/domain-based, not type-based
- **Cohesion:** high within file, low coupling between files

---

## 6. Immutability

Always create new objects — never mutate existing ones:

```python
# WRONG: mutation
lead.status = LeadStatus.MATCHED

# CORRECT: new object
updated_lead = lead.model_copy(update={"status": LeadStatus.MATCHED})
```

---

## 7. Configuration

- All environment values via `pydantic-settings` in `src/core/config.py`
- Never `os.environ.get()` directly in service or agent code
- Never hardcode URLs, ports, secrets, model names, or environment-specific values
- All required vars validated at startup — app fails fast with clear error message

---

## 8. Error Handling

- Use typed custom exceptions from `src/core/exceptions.py`
- Never expose internal stack traces or raw DB errors to API consumers
- Always return the standard error envelope
- Log detailed context server-side; return user-friendly messages to clients
- See [rules/error-observability.md](rules/error-observability.md)

---

## 9. Code Quality Checklist

Before marking any task complete:

- [ ] Code follows the layer architecture (router / service / repository)
- [ ] No hardcoded secrets, model names, URLs, or environment values
- [ ] Pydantic validation on all user-facing inputs
- [ ] Error handling present (no silent `except` blocks)
- [ ] No direct SQLAlchemy calls outside repositories
- [ ] No direct LLM API calls outside LangChain agents
- [ ] File size under 800 lines
- [ ] Functions under 50 lines
- [ ] No deeply nested logic (max 4 levels)
- [ ] Response schemas used to shape API responses
- [ ] Tests written (unit for services, integration for routers)
- [ ] Alembic migration created for any schema change
- [ ] No mutation of domain objects
- [ ] Structured logging with trace_id on key operations
- [ ] Health check endpoint present if new service added
