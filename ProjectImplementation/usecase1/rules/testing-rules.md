# Testing Rules — Usecase 1: Lead Automation Platform

> **Extends:** `project-specific-guidelines/rules/testing-rules.md`
> **Which extends:** `best-practices_rule_set_code/docs/rules/testing-rules.md`
> **Scope:** `ProjectImplementation/usecase1/` — concrete test file locations, factory definitions, and sprint-level DoD

---

## 1. Concrete Test Locations

All test files for this usecase live under `ProjectImplementation/usecase1/src/../tests/` relative to the usecase root, mirroring the `src/` tree:

```
ProjectImplementation/usecase1/
├── src/
│   ├── api/routers/leads.py
│   ├── services/lead_ingestion_service.py
│   ├── repositories/lead_repository.py
│   ├── tasks/ingestion_task.py
│   └── ai/nodes/outreach_node.py
└── tests/
    ├── conftest.py
    ├── factories/
    │   ├── lead_factory.py
    │   ├── inventory_factory.py
    │   ├── contact_factory.py
    │   ├── outreach_factory.py
    │   ├── crm_activity_factory.py
    │   └── user_factory.py
    ├── fixtures/
    │   ├── sample_leads.csv
    │   ├── sample_leads_dupes.csv
    │   └── sample_inventory.json
    ├── unit/
    │   ├── conftest.py
    │   ├── api/
    │   ├── services/
    │   ├── repositories/
    │   ├── tasks/
    │   ├── ai/
    │   └── core/
    ├── integration/
    │   ├── conftest.py
    │   └── *.py
    └── e2e/
        ├── conftest.py
        └── test_lead_lifecycle_e2e.py
```

---

## 2. Factory Definitions

### Lead Factory

```python
# tests/factories/lead_factory.py
import factory
from factory import LazyFunction
from uuid import uuid4
from datetime import datetime, timezone
from src.domain.lead import LeadCreateDTO
from src.db.models.lead_model import LeadORM, LeadStatus

class LeadDTOFactory(factory.Factory):
    class Meta:
        model = LeadCreateDTO

    company_name = factory.Sequence(lambda n: f"Test Jeweler {n:04d}")
    contact_email = factory.LazyAttribute(
        lambda o: f"buyer.{o.company_name.replace(' ', '.').lower()}@example.com"
    )
    country = factory.Iterator(["US", "AE", "IN", "UK", "SG"])
    annual_revenue_usd = factory.Faker("random_int", min=100_000, max=10_000_000)
    source = "CSV_UPLOAD"


class LeadORMFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = LeadORM
        sqlalchemy_session_persistence = "flush"

    id = LazyFunction(uuid4)
    company_name = factory.Sequence(lambda n: f"Test Jeweler {n:04d}")
    status = LeadStatus.NEW
    score = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
```

### Contact Factory

```python
# tests/factories/contact_factory.py
import factory
from uuid import uuid4
from src.db.models.contact_model import ContactORM

class ContactORMFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ContactORM
        sqlalchemy_session_persistence = "flush"

    id = LazyFunction(uuid4)
    lead_id = LazyFunction(uuid4)     # override in tests: lead_id=lead.id
    email = factory.Sequence(lambda n: f"contact{n:04d}@example.com")
    full_name = factory.Faker("name")
    title = factory.Iterator(["Buyer", "Head of Procurement", "COO", "Director"])
    phone = factory.Faker("phone_number")
    linkedin_url = factory.LazyAttribute(
        lambda o: f"https://linkedin.com/in/test-{o.id}"
    )
    enrichment_source = "APOLLO"
```

### User Factory

```python
# tests/factories/user_factory.py
import factory
from uuid import uuid4
from src.db.models.user_model import UserORM, UserRole

class UserORMFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserORM
        sqlalchemy_session_persistence = "flush"

    id = LazyFunction(uuid4)
    email = factory.Sequence(lambda n: f"user{n:04d}@example.com")
    hashed_password = "$2b$12$test_hashed_password_placeholder"
    role = UserRole.REP
    is_active = True


class AdminUserFactory(UserORMFactory):
    role = UserRole.ADMIN


class ManagerUserFactory(UserORMFactory):
    role = UserRole.MANAGER
```

---

## 3. Integration Test Database Setup

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.db.session import get_db
from src.db.base import Base
from src.core.config import get_settings

@pytest.fixture(scope="session")
def settings():
    s = get_settings()
    assert "test" in s.DATABASE_URL.lower() or "pytest" in s.DATABASE_URL.lower(), \
        "Integration tests must use a TEST database — check TEST_DATABASE_URL env var"
    return s

@pytest_asyncio.fixture(scope="function")
async def db_session(settings):
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()
```

---

## 4. Per-Epic Test Requirements

Each epic must have tests created at the same time as the implementation:

| Epic | Unit Test Files | Integration Test Files |
|---|---|---|
| EPIC-01 | `tests/unit/core/test_config.py`, `test_logging.py`, `test_exceptions.py` | `tests/integration/test_health_endpoints_integration.py` |
| EPIC-02 | `tests/unit/services/test_lead_ingestion_service.py`, `tests/unit/tasks/test_ingestion_task.py` | `tests/integration/test_lead_upload_integration.py` |
| EPIC-03 | `tests/unit/services/test_inventory_match_service.py` | `tests/integration/test_inventory_matching_integration.py` |
| EPIC-04 | `tests/unit/services/test_enrichment_service.py`, `tests/unit/tasks/test_enrichment_task.py` | `tests/integration/test_enrichment_pipeline_integration.py` |
| EPIC-05 | `tests/unit/ai/test_outreach_node.py`, `tests/unit/services/test_outreach_generation_service.py` | `tests/integration/test_outreach_generation_integration.py` |
| EPIC-06 | `tests/unit/services/test_email_delivery_service.py` | `tests/integration/test_sendgrid_webhook_integration.py` |
| EPIC-07 | `tests/unit/services/test_crm_activity_service.py` | `tests/integration/test_crm_immutability_integration.py` |
| EPIC-08 | `tests/unit/services/test_lead_scoring_service.py`, `tests/unit/tasks/test_scoring_task.py` | `tests/integration/test_scoring_pipeline_integration.py` |
| EPIC-09 | (Streamlit UI — manual E2E) | `tests/integration/test_dashboard_api_integration.py` |
| EPIC-10 | `tests/unit/tasks/test_followup_task.py` | `tests/integration/test_n8n_webhook_integration.py` |
| EPIC-11 | `tests/unit/api/test_auth_router.py` | `tests/integration/test_jwt_auth_integration.py` |
| EPIC-12 | `tests/unit/services/test_whatsapp_service.py` | `tests/integration/test_twilio_webhook_integration.py` |
| EPIC-13 | `tests/unit/ai/test_mlflow_tracking.py` | `tests/integration/test_mlflow_registration_integration.py` |
| EPIC-14 | `tests/unit/repositories/test_lead_repository_queries.py` | `tests/integration/test_rate_limiting_integration.py` |
| EPIC-15 | `tests/unit/core/test_logging.py`, `tests/unit/api/test_health_router.py` | `tests/integration/test_prometheus_metrics_integration.py` |

---

## 5. Environment Variables for Tests

Add these to `.env.test` (never commit real values):

```bash
# Test database — MUST be separate from dev DB
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/jewelry_ai_test

# Test Redis — MUST be separate from dev Redis
TEST_REDIS_URL=redis://localhost:6380/1

# JWT for test token generation
JWT_SECRET_KEY=test-jwt-secret-key-for-ci-only

# Disable external APIs in test environment
APOLLO_API_KEY=test-apollo-key
HUNTER_API_KEY=test-hunter-key
SENDGRID_API_KEY=test-sendgrid-key
OPENAI_API_KEY=test-openai-key

# Disable human review gate in tests
HUMAN_REVIEW_REQUIRED=false
```

---

## 6. CI Test Command

```bash
# Full test suite with coverage (mirrors CI gate)
pytest tests/unit/ tests/integration/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-fail-under=80 \
  -v

# Unit tests only (fast, < 30 seconds)
pytest tests/unit/ -v

# Integration tests only (requires Docker services)
pytest tests/integration/ -m integration -v

# E2E tests (full stack — Docker Compose must be running)
pytest tests/e2e/ -m e2e -v --timeout=120
```

---

## 7. Usecase1-Specific Testing DoD

In addition to the project-wide testing DoD, this usecase requires:

- [ ] All CSV upload tests use `tests/fixtures/sample_leads.csv` — not inline strings
- [ ] All enrichment tests mock both Apollo AND Hunter fallback paths
- [ ] CRM activity immutability verified in at least one integration test per epic that writes activities
- [ ] JWT auth tests cover all three roles (admin, manager, rep) per protected endpoint
- [ ] Celery tasks tested in eager mode — no real broker required in CI
- [ ] LangGraph nodes tested with `OutreachGraphState` objects built via factory
- [ ] Coverage report artifact uploaded in CI: `--cov-report=xml:coverage.xml`
