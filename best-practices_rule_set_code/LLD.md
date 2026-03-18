# Low-Level Design (LLD) — Template

> **Generic template — no project-specific content.**
> Replace `<Entity>`, `<entity>`, `<field>`, and all `<placeholder>` values with your project's specifics.

---

## 1. Database Schema

### Core Table Pattern

Every table MUST follow this structure (UUID PK, soft deletes, audit timestamps):

```sql
CREATE TABLE <entities> (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- <domain fields here>
    status          VARCHAR(50) NOT NULL DEFAULT '<initial_status>',
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(100)
);

CREATE INDEX idx_<entities>_status ON <entities>(status);
```

### Primary Entity: `<entities>`

```sql
CREATE TABLE <entities> (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    <field_a>       VARCHAR(255) NOT NULL,
    <field_b>       VARCHAR(255),
    <field_c>       VARCHAR(100),
    status          VARCHAR(50) NOT NULL DEFAULT '<initial_status>',
                                                   -- <list status values>
    score           FLOAT,                         -- optional ML score field
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(100)
);

CREATE INDEX idx_<entities>_status ON <entities>(status);
CREATE INDEX idx_<entities>_score ON <entities>(score DESC);
```

### Related Entity: `<related_entities>`

```sql
CREATE TABLE <related_entities> (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    <parent>_id     UUID NOT NULL REFERENCES <entities>(id),
    <field_a>       VARCHAR(255),
    <field_b>       VARCHAR(255),
    <field_c>       BOOLEAN DEFAULT false,
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_<related_entities>_<parent>_<key>
    ON <related_entities>(<parent>_id, <key_field>);
```

### Junction Table: `<entity_a>_<entity_b>_matches`

```sql
CREATE TABLE <entity_a>_<entity_b>_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    <entity_a>_id   UUID NOT NULL REFERENCES <entity_a>(id),
    <entity_b>_id   UUID NOT NULL REFERENCES <entity_b>(id),
    match_score     FLOAT NOT NULL,
    match_reason    TEXT,                          -- JSON: which rules matched
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Activity Log (Append-Only)

```sql
CREATE TABLE <domain>_activity (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    <parent>_id     UUID NOT NULL REFERENCES <entities>(id),
    event_type      VARCHAR(100) NOT NULL,
    event_payload   JSONB,
    agent           VARCHAR(100),                  -- system, user:<name>, agent:<type>
    trace_id        VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- NOTE: No updated_at — this table is append-only, never updated
);

CREATE INDEX idx_<domain>_activity_<parent>_id ON <domain>_activity(<parent>_id);
CREATE INDEX idx_<domain>_activity_event_type ON <domain>_activity(event_type);
```

---

## 2. API Endpoints (FastAPI)

### Primary Resource

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/<entities>/upload` | Upload file of records (CSV/Excel) |
| `GET` | `/api/v1/<entities>` | List with filters (status, source, date range) |
| `GET` | `/api/v1/<entities>/{id}` | Get full record detail with relations |
| `PATCH` | `/api/v1/<entities>/{id}/status` | Manually update status |
| `DELETE` | `/api/v1/<entities>/{id}` | Soft-delete a record |

### Related Resource

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/<related>` | Create a related record |
| `GET` | `/api/v1/<related>` | List related records with filters |
| `PUT` | `/api/v1/<related>/{id}` | Update a related record |

### Async Operations

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/<operations>/{id}` | Trigger async operation for single record |
| `POST` | `/api/v1/<operations>/batch` | Trigger bulk async operation |
| `GET` | `/api/v1/<operations>/status/{job_id}` | Poll Celery job status |

### Output / Generation

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/<outputs>/generate/{id}` | Generate output (AI/ML) for a record |
| `POST` | `/api/v1/<outputs>/send/{output_id}` | Send/deliver an approved output |
| `GET` | `/api/v1/<outputs>` | List all generated outputs |
| `PATCH` | `/api/v1/<outputs>/{output_id}` | Edit a draft output |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/analytics/funnel` | Pipeline funnel metrics by stage |
| `GET` | `/api/v1/analytics/<metric>` | Domain-specific performance metric |
| `GET` | `/api/v1/activity/{id}` | Full activity timeline for a record |

---

## 3. Domain Models (Pydantic)

```python
# src/domain/<entity>.py

from enum import Enum
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


class EntityStatus(str, Enum):
    CREATED = "<initial>"
    PROCESSING = "<step_2>"
    PROCESSED = "<step_3>"
    COMPLETED = "<final>"
    FAILED = "failed"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"


class Entity(BaseModel):
    id: UUID | None = None
    <field_a>: str
    <field_b>: str | None = None
    <field_c>: str | None = None
    source: str
    status: EntityStatus = EntityStatus.CREATED
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    score: float | None = None
    is_deleted: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("<field_a>")
    @classmethod
    def field_a_must_not_be_empty(cls, value: str) -> str:
        """Ensure <field_a> is non-empty after stripping whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("<field_a> cannot be empty")
        return stripped
```

---

## 4. LangGraph Workflow — Core Pipeline

### Node Definitions

```python
# src/agents/workflows/<pipeline_name>.py


async def check_eligibility_node(state: WorkflowState) -> WorkflowState:
    """
    Node: Check entity eligibility against configured rules.

    Updates state with is_eligible flag.
    """
    result = await matching_service.check(state["entity_id"])
    return {**state, "is_eligible": result.is_eligible}


async def process_step_a_node(state: WorkflowState) -> WorkflowState:
    """
    Node: Execute Step A processing (e.g., external enrichment).

    Falls back to secondary provider on primary failure.
    """
    try:
        await processing_service.execute(state["entity_id"])
        return {**state, "step_a_complete": True}
    except IntegrationException as exc:
        logger.error(
            "Step A failed",
            extra={"entity_id": state["entity_id"], "error": str(exc)}
        )
        return {**state, "step_a_complete": False, "error": str(exc)}


async def generate_output_node(state: WorkflowState) -> WorkflowState:
    """
    Node: Generate output via LLM or ML model.

    If HUMAN_REVIEW_REQUIRED is True in config, creates draft only.
    Otherwise delivers immediately.
    """
    output = await output_service.generate_and_deliver(state["entity_id"])
    return {**state, "output_delivered": output.status != "draft"}
```

---

## 5. Celery Task Definitions

```python
# src/tasks/<domain>_tasks.py

from src.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="<queue_name>"
)
def process_entity_task(self, entity_id: str) -> dict:
    """
    Celery task: Process a single entity asynchronously.

    Retried up to 3 times on IntegrationException with 60-second delay.

    Args:
        entity_id (str): UUID string of the entity to process.

    Returns:
        dict: Result summary with processing status and output ID.
    """
    import asyncio
    try:
        result = asyncio.run(processing_service.process(entity_id))
        return {
            "status": "success",
            "entity_id": entity_id,
            "output_id": str(result.id)
        }
    except IntegrationException as exc:
        raise self.retry(exc=exc)
```

---

## 6. ML Model Design

### Feature Engineering

| Feature | Source | Type |
|---|---|---|
| `<feature_a>` | `<source_table>` | Categorical |
| `<feature_b>` | `<external_api>` | Ordinal (0–N) |
| `<feature_c>` | `<matching_engine>` | Float |
| `<feature_d>` | `<verification_api>` | Boolean |
| `<feature_e>` | `<activity_log>` | Integer |

### Model Training Guidelines
- Choose algorithm appropriate to the prediction task (classification/regression)
- Define minimum evaluation metric threshold before deployment
- Use MLflow for experiment tracking: runs, hyperparameters, metrics, artifacts
- Version all models in MLflow Model Registry before promoting to production

---

## 7. LLM Prompt Design Pattern

```python
SYSTEM_PROMPT = """
You are a <role description> at <company type>.
You <describe the task the LLM should perform>.
Your tone is <tone description>. Never exceed <N> words.
<Domain-specific instructions>.
<Output format instructions>.
"""

USER_PROMPT = """
<Entity Type>: {entity_name}
<Context Field A>: {context_a}
<Context Field B>: {context_b}
<Context Field C>: {context_c}

<Reference Data>:
{reference_items}

<Task instruction for this specific request>.
"""
```

### Prompt Design Rules
- System prompt sets the persona, constraints, and format — never changes per request
- User prompt injects dynamic context — always sanitize before interpolation
- Set explicit `max_tokens` to control cost and output length
- Define output format clearly (JSON, plain text, specific structure) to enable parsing

---

## 8. Error Response Schema

All API error responses follow this structure:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ENTITY_NOT_FOUND",
  "detail": "Entity with ID <id> does not exist",
  "trace_id": "req-<correlation-id>"
}
```

### Standard Error Codes

| Code | HTTP Status | Meaning |
|---|---|---|
| `<ENTITY>_NOT_FOUND` | 404 | Resource does not exist or is soft-deleted |
| `<ENTITY>_VALIDATION_ERROR` | 422 | Request body failed schema validation |
| `DUPLICATE_<ENTITY>` | 409 | Record already exists (deduplication) |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT token |
| `FORBIDDEN` | 403 | Valid token but insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests — retry after cooldown |
| `INTEGRATION_ERROR` | 502 | External API call failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error — check trace_id in logs |

---

## 9. Configuration Schema (`.env.example`)

```env
# Application
APP_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=<your-secret-key-here>

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/<db_name>
REDIS_URL=redis://localhost:6379/0

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# External Integrations
<PROVIDER_A>_API_KEY=...
<PROVIDER_B>_API_KEY=...
<PROVIDER_C>_API_KEY=...

# Delivery
<DELIVERY_PROVIDER>_API_KEY=...
<DELIVERY_PROVIDER>_FROM_ADDRESS=<sender@domain.com>

# Workflow Engine
<WORKFLOW_ENGINE>_WEBHOOK_URL=http://localhost:<PORT>/webhook/...

# Feature Flags
HUMAN_REVIEW_REQUIRED=true
MAX_BATCH_SIZE=500
<CUSTOM_THRESHOLD>=<default_value>
```
