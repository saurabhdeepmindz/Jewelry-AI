# Low-Level Design (LLD) — Jewelry AI Platform

## 1. Database Schema

### Table: `leads`
```sql
CREATE TABLE leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name    VARCHAR(255) NOT NULL,
    domain          VARCHAR(255),
    country         VARCHAR(100),
    state           VARCHAR(100),
    city            VARCHAR(100),
    phone           VARCHAR(50),
    website         VARCHAR(255),
    source          VARCHAR(100) NOT NULL,         -- gmt, trade_book, rapid_list, manual
    status          VARCHAR(50) NOT NULL DEFAULT 'ingested',
                                                   -- ingested, matched, enriched, contacted, responded, closed
    match_status    VARCHAR(50) DEFAULT 'pending', -- pending, eligible, not_eligible
    score           FLOAT,                         -- 0.0 - 100.0 from ML model
    embedding       VECTOR(1536),                  -- pgvector for semantic dedup
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(100)
);

CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_match_status ON leads(match_status);
CREATE INDEX idx_leads_score ON leads(score DESC);
```

### Table: `inventory`
```sql
CREATE TABLE inventory (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             VARCHAR(100) UNIQUE NOT NULL,
    stone_type      VARCHAR(50) NOT NULL,          -- diamond, sapphire, ruby, etc.
    shape           VARCHAR(50) NOT NULL,           -- RBC, princess, oval, etc.
    carat_weight    DECIMAL(6,2) NOT NULL,
    color_grade     VARCHAR(10),                    -- D, E, F, G, H ...
    clarity_grade   VARCHAR(10),                    -- IF, VVS1, VVS2, VS1 ...
    cut_grade       VARCHAR(20),                    -- Excellent, Very Good, Good
    certification   VARCHAR(50),                    -- GIA, IGI, HRD
    cert_number     VARCHAR(100),
    price_usd       DECIMAL(12,2),
    is_available    BOOLEAN NOT NULL DEFAULT true,
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Table: `lead_inventory_matches`
```sql
CREATE TABLE lead_inventory_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    inventory_id    UUID NOT NULL REFERENCES inventory(id),
    match_score     FLOAT NOT NULL,               -- rule-based match quality
    match_reason    TEXT,                          -- JSON: which rules matched
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Table: `contacts`
```sql
CREATE TABLE contacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    full_name       VARCHAR(255),
    title           VARCHAR(255),
    email           VARCHAR(255),
    email_verified  BOOLEAN DEFAULT false,
    phone           VARCHAR(50),
    linkedin_url    VARCHAR(500),
    enrichment_source VARCHAR(50),               -- apollo, hunter, linkedin, manual
    enriched_at     TIMESTAMPTZ,
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_contacts_lead_email ON contacts(lead_id, email);
```

### Table: `outreach_messages`
```sql
CREATE TABLE outreach_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    contact_id      UUID REFERENCES contacts(id),
    channel         VARCHAR(50) NOT NULL,          -- email, whatsapp, linkedin
    subject         VARCHAR(500),
    body            TEXT NOT NULL,
    sequence_step   INTEGER NOT NULL DEFAULT 1,
    status          VARCHAR(50) NOT NULL DEFAULT 'draft',
                                                   -- draft, pending_review, sent, opened, clicked, replied, bounced
    sendgrid_message_id VARCHAR(255),
    sent_at         TIMESTAMPTZ,
    opened_at       TIMESTAMPTZ,
    replied_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Table: `crm_activity`
```sql
CREATE TABLE crm_activity (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    event_type      VARCHAR(100) NOT NULL,         -- lead_ingested, matched, enriched, email_sent, reply_received
    event_payload   JSONB,
    agent           VARCHAR(100),                  -- system, user:john, agent:enrichment
    trace_id        VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_crm_activity_lead_id ON crm_activity(lead_id);
CREATE INDEX idx_crm_activity_event_type ON crm_activity(event_type);
```

---

## 2. API Endpoints (FastAPI)

### Leads

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/leads/upload` | Upload CSV/Excel file of leads |
| `GET` | `/api/v1/leads` | List leads with filters (status, match_status, source) |
| `GET` | `/api/v1/leads/{lead_id}` | Get full lead detail with contact + matches |
| `PATCH` | `/api/v1/leads/{lead_id}/status` | Manually update lead status |
| `DELETE` | `/api/v1/leads/{lead_id}` | Soft-delete a lead |

### Inventory

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/inventory/upload` | Upload inventory file |
| `GET` | `/api/v1/inventory` | List inventory with filters |
| `PUT` | `/api/v1/inventory/{sku}` | Update inventory item |
| `POST` | `/api/v1/inventory/match-rules` | Configure match rules |

### Enrichment

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/enrichment/{lead_id}` | Trigger enrichment for single lead |
| `POST` | `/api/v1/enrichment/batch` | Trigger bulk enrichment job |
| `GET` | `/api/v1/enrichment/status/{job_id}` | Poll Celery job status |

### Outreach

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/outreach/generate/{lead_id}` | Generate outreach draft for lead |
| `POST` | `/api/v1/outreach/send/{message_id}` | Send approved outreach message |
| `GET` | `/api/v1/outreach/messages` | List all outreach messages |
| `PATCH` | `/api/v1/outreach/messages/{message_id}` | Edit draft message |

### CRM & Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/crm/timeline/{lead_id}` | Full activity timeline for a lead |
| `GET` | `/api/v1/analytics/funnel` | Pipeline funnel metrics |
| `GET` | `/api/v1/analytics/outreach-performance` | Email open/reply/click metrics |

---

## 3. Domain Models (Pydantic)

```python
# src/domain/lead.py

from enum import Enum
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class LeadStatus(str, Enum):
    INGESTED = "ingested"
    MATCHED = "matched"
    ENRICHED = "enriched"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CLOSED = "closed"


class MatchStatus(str, Enum):
    PENDING = "pending"
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"


class Lead(BaseModel):
    id: UUID | None = None
    company_name: str
    domain: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    phone: str | None = None
    source: str
    status: LeadStatus = LeadStatus.INGESTED
    match_status: MatchStatus = MatchStatus.PENDING
    score: float | None = None
    is_deleted: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("company_name")
    @classmethod
    def company_name_must_not_be_empty(cls, value: str) -> str:
        """Ensure company_name is non-empty after stripping whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("company_name cannot be empty")
        return stripped
```

---

## 4. LangGraph Workflow — Lead Pipeline

### Node Definitions

```python
# src/agents/workflows/lead_pipeline.py

async def match_inventory_node(state: LeadPipelineState) -> LeadPipelineState:
    """
    Node: Match lead against inventory using configured rules.

    Queries inventory_match_service to determine eligibility.
    Updates state with is_eligible flag.
    """
    result = await inventory_match_service.match(state["lead_id"])
    return {**state, "is_eligible": result.is_eligible}


async def enrich_contact_node(state: LeadPipelineState) -> LeadPipelineState:
    """
    Node: Enrich contact details via Apollo.io.

    Calls enrichment agent. Marks contact_enriched in state.
    Falls back to Hunter.io on Apollo failure.
    """
    try:
        await enrichment_service.enrich_lead(state["lead_id"])
        return {**state, "contact_enriched": True}
    except IntegrationException as exc:
        logger.error("Enrichment failed", extra={"lead_id": state["lead_id"], "error": str(exc)})
        return {**state, "contact_enriched": False, "error": str(exc)}


async def send_outreach_node(state: LeadPipelineState) -> LeadPipelineState:
    """
    Node: Generate and optionally send personalized outreach.

    If human_review_required is True in config, creates draft only.
    Otherwise sends immediately via SendGrid.
    """
    message = await outreach_service.generate_and_send(state["lead_id"])
    return {**state, "outreach_sent": message.status != "draft"}
```

---

## 5. Celery Task Definitions

```python
# src/tasks/enrichment_tasks.py

from src.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="enrichment"
)
def enrich_lead_task(self, lead_id: str) -> dict:
    """
    Celery task: Enrich a single lead asynchronously.

    Runs the enrichment LangGraph workflow for the given lead.
    Retried up to 3 times on IntegrationException.

    Args:
        lead_id (str): UUID string of the lead to enrich.

    Returns:
        dict: Result summary with enrichment status and contact ID.
    """
    import asyncio
    try:
        result = asyncio.run(enrichment_service.enrich_lead(lead_id))
        return {"status": "success", "lead_id": lead_id, "contact_id": str(result.id)}
    except IntegrationException as exc:
        raise self.retry(exc=exc)
```

---

## 6. Lead Scoring Model (ML)

### Features
| Feature | Source | Type |
|---|---|---|
| company_country | Lead | Categorical |
| company_size_bucket | Apollo | Categorical (0–5) |
| buyer_title_seniority | Apollo | Ordinal (0–3) |
| inventory_match_score | MatchEngine | Float |
| email_verified | Hunter | Boolean |
| linkedin_enriched | LinkedIn | Boolean |
| source_type | Lead | Categorical |
| days_since_last_contact | CRM | Integer |

### Model Training
- Algorithm: XGBoost Classifier (binary: converted / not converted)
- Training data: historical CRM outcomes (replied + purchased = positive)
- Evaluation: AUC-ROC ≥ 0.75 before deployment
- MLflow tracking: experiment runs, hyperparameters, metrics, model artifacts

---

## 7. LLM Outreach Generation Prompt Design

```python
OUTREACH_SYSTEM_PROMPT = """
You are a senior sales executive at Shivam Jewels, a premium diamond wholesaler.
You write personalized, professional outreach emails to jewelry buyers.
Your tone is warm, authoritative, and concise. Never exceed 150 words.
Reference specific diamonds from the inventory provided.
End with a clear, low-pressure call to action.
"""

OUTREACH_USER_PROMPT = """
Lead Company: {company_name}
Buyer Name: {buyer_name}, {buyer_title}
Location: {city}, {country}

Matched Inventory:
{inventory_items}

Write a personalized outreach email for this buyer.
"""
```

---

## 8. Error Response Schema

All API error responses follow this structure:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "LEAD_NOT_FOUND",
  "detail": "Lead with ID abc123 does not exist",
  "trace_id": "req-xyz789"
}
```

---

## 9. Configuration Schema (`.env.example`)

```env
# Application
APP_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/jewelry_ai
REDIS_URL=redis://localhost:6379/0

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Enrichment APIs
APOLLO_API_KEY=...
HUNTER_API_KEY=...
PROXYCURL_API_KEY=...

# Outreach
SENDGRID_API_KEY=SG....
SENDGRID_FROM_EMAIL=sales@shivamjewels.com
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...

# n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook/...

# Feature Flags
HUMAN_REVIEW_REQUIRED=true
MAX_BATCH_SIZE=500
INVENTORY_MATCH_MIN_CARAT=0.50
```
