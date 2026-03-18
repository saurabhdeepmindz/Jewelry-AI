# Testing Rules — Jewelry AI Project-Specific

> **Extends:** `best-practices_rule_set_code/docs/rules/testing-rules.md`
> **Scope:** Jewelry AI Lead Automation Platform — project-wide testing rules
> **All generic rules apply.** This file adds project-specific patterns, libraries, and domain requirements.

---

## 1. Testing Stack (Jewelry AI)

| Library | Version | Purpose |
|---|---|---|
| `pytest` | ≥8.0 | Test runner |
| `pytest-asyncio` | ≥0.23 | Async test support |
| `pytest-cov` | ≥5.0 | Coverage reporting |
| `pytest-mock` | ≥3.12 | `mocker` fixture |
| `factory_boy` | ≥3.3 | Domain object factories |
| `httpx` | ≥0.27 | HTTP client (prod + test) |
| `respx` | ≥0.21 | Mock httpx transport |
| `freezegun` | ≥1.4 | Freeze time in tests |
| `faker` | ≥25.0 | Realistic fake data |

**All testing dependencies go in `pyproject.toml` under `[project.optional-dependencies] dev`.**

---

## 2. Test Directory Structure

```
tests/
├── conftest.py                    ← Root: db_session, async_client, auth_headers, settings
├── factories/
│   ├── __init__.py
│   ├── lead_factory.py            ← LeadDTOFactory, LeadORMFactory
│   ├── inventory_factory.py       ← InventoryDTOFactory, InventoryORMFactory
│   ├── contact_factory.py         ← ContactDTOFactory, ContactORMFactory
│   ├── outreach_factory.py        ← OutreachMessageFactory
│   ├── crm_activity_factory.py    ← CRMActivityFactory (append-only)
│   └── user_factory.py            ← UserFactory (admin, manager, rep roles)
├── fixtures/
│   ├── sample_leads.csv           ← Valid CSV for upload tests
│   ├── sample_leads_dupes.csv     ← CSV with duplicates for dedup tests
│   └── sample_inventory.json     ← Inventory seed for matching tests
├── unit/
│   ├── conftest.py
│   ├── services/
│   │   ├── test_lead_ingestion_service.py
│   │   ├── test_inventory_match_service.py
│   │   ├── test_enrichment_service.py
│   │   ├── test_outreach_generation_service.py
│   │   ├── test_email_delivery_service.py
│   │   ├── test_lead_scoring_service.py
│   │   └── test_crm_activity_service.py
│   ├── repositories/
│   │   ├── test_lead_repository.py
│   │   └── test_contact_repository.py
│   ├── api/
│   │   ├── test_leads_router.py
│   │   ├── test_auth_router.py
│   │   └── test_outreach_router.py
│   ├── tasks/
│   │   ├── test_ingestion_task.py
│   │   ├── test_enrichment_task.py
│   │   ├── test_scoring_task.py
│   │   └── test_outreach_task.py
│   └── core/
│       ├── test_config.py
│       └── test_logging.py
├── integration/
│   ├── conftest.py
│   ├── test_lead_upload_integration.py
│   ├── test_enrichment_pipeline_integration.py
│   ├── test_outreach_generation_integration.py
│   ├── test_jwt_auth_integration.py
│   ├── test_rate_limiting_integration.py
│   └── test_health_endpoints_integration.py
└── e2e/
    ├── conftest.py
    └── test_lead_lifecycle_e2e.py
```

---

## 3. Domain-Specific Testing Rules

### 3.1 CRM Activity — Append-Only Enforcement

CRM activity rows are **immutable** by design. Tests must verify this:

```python
async def test_crm_activity_cannot_be_updated(db_session):
    """CRM activity rows must never be updatable."""
    activity = CRMActivityFactory.build()
    db_session.add(activity)
    await db_session.commit()

    # Attempt update must raise — enforced at service layer
    with pytest.raises(ImmutableRecordError):
        await crm_service.update_activity(activity.id, new_note="changed")

async def test_crm_activity_cannot_be_deleted(db_session):
    """CRM activity rows must never be deletable."""
    activity = CRMActivityFactory.build()
    db_session.add(activity)
    await db_session.commit()

    with pytest.raises(ImmutableRecordError):
        await crm_service.delete_activity(activity.id)
```

### 3.2 Enrichment Cache — Cache-Before-API Pattern

Every enrichment test must verify the cache-first pattern:

```python
@respx.mock
async def test_enrichment_uses_cache_hit_skips_api(mock_redis, mocker):
    """If a cache hit exists, the Apollo API must NOT be called."""
    mock_redis.get.return_value = cached_contact_json()
    apollo_mock = respx.post("https://api.apollo.io/v1/people/match")

    await enrichment_service.enrich_lead(lead_id="test-id")

    assert not apollo_mock.called
    mock_redis.get.assert_called_once()

@respx.mock
async def test_enrichment_caches_result_after_api_call(mock_redis):
    """After a successful Apollo call, result must be written to Redis."""
    respx.post("https://api.apollo.io/v1/people/match").mock(
        return_value=httpx.Response(200, json=apollo_success_response())
    )
    mock_redis.get.return_value = None  # cache miss

    await enrichment_service.enrich_lead(lead_id="test-id")

    mock_redis.setex.assert_called_once()
```

### 3.3 Lead Eligibility — Business Rule Tests

```python
@pytest.mark.parametrize("match_count,expected", [
    (0, False),   # No inventory match → not eligible
    (1, True),    # At least one match → eligible
    (5, True),    # Many matches → eligible
])
async def test_lead_eligibility_requires_inventory_match(
    match_count, expected, ingestion_service
):
    lead = LeadORMFactory.build()
    matches = [InventoryMatchFactory.build(lead_id=lead.id) for _ in range(match_count)]
    result = ingestion_service.compute_eligibility(lead, matches)
    assert result.is_eligible == expected
```

### 3.4 JWT Auth — Role-Based Access Tests

Every protected endpoint must have auth tests:

```python
class TestLeadsRouterAuth:

    async def test_rep_can_view_assigned_leads(self, async_client, rep_headers):
        response = await async_client.get("/api/v1/leads/", headers=rep_headers)
        assert response.status_code == 200

    async def test_rep_cannot_approve_outreach(self, async_client, rep_headers):
        response = await async_client.post(
            "/api/v1/outreach/123/approve", headers=rep_headers
        )
        assert response.status_code == 403

    async def test_unauthenticated_request_returns_401(self, async_client):
        response = await async_client.get("/api/v1/leads/")
        assert response.status_code == 401

    async def test_expired_token_returns_401(self, async_client, expired_token_headers):
        response = await async_client.get("/api/v1/leads/", headers=expired_token_headers)
        assert response.status_code == 401
```

---

## 4. Celery Task Testing

Celery tasks must be testable in **eager mode** (synchronous, no broker needed):

```python
# tests/unit/tasks/test_ingestion_task.py
from unittest.mock import patch, AsyncMock
from src.tasks.ingestion_task import process_csv_upload

def test_ingestion_task_calls_service_with_job_id(mocker):
    """Task must call ingestion service with correct job_id."""
    mock_service = mocker.patch(
        "src.tasks.ingestion_task.LeadIngestionService.process_file",
        new_callable=AsyncMock,
        return_value=IngestionResultFactory.build(),
    )
    # Call task directly in eager mode (no Celery worker needed)
    process_csv_upload.apply(args=["job-123", "/tmp/test.csv"])

    mock_service.assert_awaited_once_with(job_id="job-123", filepath="/tmp/test.csv")

def test_ingestion_task_logs_trace_id_on_failure(mocker, caplog):
    """On failure, task must log the trace_id for correlation."""
    mocker.patch(
        "src.tasks.ingestion_task.LeadIngestionService.process_file",
        side_effect=ValueError("bad file"),
    )
    with pytest.raises(ValueError):
        process_csv_upload.apply(args=["job-456", "/tmp/bad.csv"])

    assert "job-456" in caplog.text
```

**Celery Task Testing Rules:**
- Always use `.apply()` for synchronous eager execution in unit tests
- Never require a real broker (Redis/RabbitMQ) for unit tests
- Test: task calls service with correct args, task handles service exceptions, task logs trace_id

---

## 5. LangGraph Node Testing

LangGraph nodes are pure functions: `state_in → state_out`. Test them directly:

```python
# tests/unit/ai/test_outreach_node.py
async def test_draft_email_node_populates_draft_field():
    """Node must populate draft_email in state without side effects."""
    state = OutreachGraphState(
        lead_id="test-lead",
        contact=ContactFactory.build(),
        inventory_matches=[InventoryMatchFactory.build()],
        draft_email=None,  # empty before node runs
    )
    with patch("src.ai.nodes.outreach_node.llm") as mock_llm:
        mock_llm.ainvoke.return_value = AIMessage(content="Subject: ...\n\nDear Buyer,...")
        new_state = await draft_email_node(state)

    assert new_state.draft_email is not None
    assert "Dear Buyer" in new_state.draft_email.body

async def test_draft_email_node_does_not_mutate_input_state():
    """Nodes must return new state; input state must be unchanged."""
    original = OutreachGraphState(lead_id="test", draft_email=None, ...)
    new_state = await draft_email_node(original)
    assert original.draft_email is None        # unchanged
    assert new_state is not original            # new object
```

**LangGraph Testing Rules:**
- Each node is tested in isolation with a pre-built `GraphState` input
- State objects must be immutable — verify that input state is not mutated
- Mock the LLM at the `llm.ainvoke` level — never call real OpenAI in unit tests
- Test: happy path produces correct state fields; error path raises correct exception

---

## 6. Structured Logging Tests

```python
async def test_request_logs_contain_trace_id(async_client, caplog):
    """Every request log line must include the trace_id."""
    import logging
    with caplog.at_level(logging.INFO, logger="jewelry_ai"):
        response = await async_client.get(
            "/api/v1/leads/",
            headers={"X-Trace-ID": "abc-123", **auth_headers("rep")},
        )
    assert response.status_code == 200
    assert all("abc-123" in record.message for record in caplog.records if record.name.startswith("jewelry_ai"))

async def test_generated_trace_id_returned_in_response_header(async_client):
    """If no X-Trace-ID is sent, one must be generated and returned."""
    response = await async_client.get("/api/v1/leads/", headers=auth_headers("rep"))
    assert "X-Trace-ID" in response.headers
    assert len(response.headers["X-Trace-ID"]) == 36  # UUID4 format
```

---

## 7. External API Integration Testing

Use `respx` for all external API mocks. Key integrations to test:

| Integration | Mock Pattern | Key Scenarios |
|---|---|---|
| Apollo.io | `respx.post(APOLLO_URL)` | 200 OK, 429 rate limit, 404 not found |
| Hunter.io | `respx.get(HUNTER_URL)` | 200 OK, 401 invalid key |
| SendGrid | `respx.post(SENDGRID_URL)` | 202 accepted, 400 invalid recipient |
| Twilio | `respx.post(TWILIO_URL)` | 201 created, 400 bad number |
| n8n webhook | `respx.post(N8N_WEBHOOK_URL)` | 200 OK, 500 server error |

---

## 8. Auth Fixtures

```python
# tests/conftest.py — auth header helpers
import pytest
from jose import jwt
from src.core.config import get_settings

@pytest.fixture
def auth_headers():
    """Factory fixture that returns headers for any role."""
    settings = get_settings()

    def _make_headers(role: str, user_id: str = "test-user") -> dict[str, str]:
        token = jwt.encode(
            {"sub": user_id, "role": role, "exp": int(time.time()) + 3600},
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    return _make_headers

@pytest.fixture
def expired_token_headers(auth_headers):
    settings = get_settings()
    token = jwt.encode(
        {"sub": "test-user", "role": "rep", "exp": int(time.time()) - 1},
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}
```

---

## 9. Performance Benchmarks in Tests

For N+1 elimination (US-049), test query counts using SQLAlchemy echo:

```python
async def test_lead_list_issues_exactly_2_queries(db_session, query_counter):
    """Lead list must not issue N+1 queries."""
    # Seed 20 leads with 3 contacts each
    leads = [LeadORMFactory.create(session=db_session) for _ in range(20)]
    for lead in leads:
        [ContactORMFactory.create(session=db_session, lead_id=lead.id) for _ in range(3)]
    await db_session.commit()

    with query_counter() as counter:
        await lead_repository.list_by_status(status=LeadStatus.NEW, limit=20)

    assert counter.count == 2  # 1 for leads, 1 for all contacts via selectinload
```

---

## 10. Definition of Done — Testing Gate

A user story is **NOT complete** until all of the following pass:

- [ ] `pytest tests/unit/` — zero failures
- [ ] `pytest tests/integration/ -m integration` — zero failures
- [ ] `pytest --cov=src --cov-fail-under=80` — coverage ≥ 80%
- [ ] `ruff check tests/` — zero lint errors
- [ ] `mypy tests/` — zero type errors
- [ ] All external API calls are mocked — no real HTTP in CI
- [ ] All test emails use `@example.com` domains
- [ ] No hardcoded secrets in test code
