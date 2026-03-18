# Low-Level Design (LLD) — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 3.3 — Architecture
**Created:** 2026-03-18
**Input:** Architecture.md, DB_SCHEMA.md, FUNCTIONAL_LANDSCAPE.md

---

## 1. Domain Models (Pydantic)

### Lead

```python
# src/domain/lead.py
from enum import Enum
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


class LeadStatus(str, Enum):
    INGESTED   = "ingested"
    MATCHED    = "matched"
    ENRICHED   = "enriched"
    SCORED     = "scored"
    CONTACTED  = "contacted"
    RESPONDED  = "responded"
    CLOSED     = "closed"


class MatchStatus(str, Enum):
    PENDING      = "pending"
    ELIGIBLE     = "eligible"
    NOT_ELIGIBLE = "not_eligible"


class ScoreTier(str, Enum):
    HIGH   = "high"    # score >= 70
    MEDIUM = "medium"  # score 40–69
    LOW    = "low"     # score < 40


class Lead(BaseModel):
    id:           UUID | None = None
    company_name: str
    domain:       str | None = None
    country:      str | None = None
    state:        str | None = None
    city:         str | None = None
    phone:        str | None = None
    website:      str | None = None
    source:       str
    status:       LeadStatus   = LeadStatus.INGESTED
    match_status: MatchStatus  = MatchStatus.PENDING
    score:        float | None = None
    score_tier:   ScoreTier | None = None
    assigned_to:  UUID | None = None
    is_deleted:   bool = False
    created_at:   datetime | None = None
    updated_at:   datetime | None = None

    @field_validator("company_name")
    @classmethod
    def company_name_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("company_name cannot be empty")
        return stripped

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 100.0):
            raise ValueError("score must be between 0.0 and 100.0")
        return v
```

### Contact

```python
# src/domain/contact.py
class ContactSource(str, Enum):
    APOLLO    = "apollo"
    HUNTER    = "hunter"
    PROXYCURL = "proxycurl"
    MANUAL    = "manual"


class Contact(BaseModel):
    id:                 UUID | None = None
    lead_id:            UUID
    full_name:          str | None = None
    title:              str | None = None
    email:              str | None = None
    email_verified:     bool = False
    phone:              str | None = None
    linkedin_url:       str | None = None
    enrichment_source:  ContactSource | None = None
    enriched_at:        datetime | None = None
    is_deleted:         bool = False
    created_at:         datetime | None = None
    updated_at:         datetime | None = None
```

### OutreachMessage

```python
# src/domain/outreach.py
class OutreachStatus(str, Enum):
    DRAFT          = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED       = "approved"
    SENT           = "sent"
    OPENED         = "opened"
    CLICKED        = "clicked"
    REPLIED        = "replied"
    BOUNCED        = "bounced"
    REJECTED       = "rejected"


class Channel(str, Enum):
    EMAIL     = "email"
    WHATSAPP  = "whatsapp"
    LINKEDIN  = "linkedin"


class OutreachMessage(BaseModel):
    id:                 UUID | None = None
    lead_id:            UUID
    contact_id:         UUID | None = None
    channel:            Channel = Channel.EMAIL
    subject:            str | None = None
    body:               str
    sequence_step:      int = 1
    status:             OutreachStatus = OutreachStatus.DRAFT
    rejection_reason:   str | None = None
    approved_by:        UUID | None = None
    approved_at:        datetime | None = None
    sendgrid_message_id: str | None = None
    sent_at:            datetime | None = None
    opened_at:          datetime | None = None
    replied_at:         datetime | None = None
    is_deleted:         bool = False
    created_at:         datetime | None = None
    updated_at:         datetime | None = None
```

### CRMActivity

```python
# src/domain/crm.py
class ActivityType(str, Enum):
    LEAD_INGESTED       = "lead_ingested"
    LEAD_MATCHED        = "lead_matched"
    LEAD_NOT_ELIGIBLE   = "lead_not_eligible"
    LEAD_ENRICHED       = "lead_enriched"
    LEAD_SCORED         = "lead_scored"
    OUTREACH_DRAFTED    = "outreach_drafted"
    OUTREACH_APPROVED   = "outreach_approved"
    OUTREACH_REJECTED   = "outreach_rejected"
    OUTREACH_SENT       = "outreach_sent"
    EMAIL_OPENED        = "email_opened"
    EMAIL_CLICKED       = "email_clicked"
    EMAIL_REPLIED       = "email_replied"
    EMAIL_BOUNCED       = "email_bounced"
    MANUAL_NOTE         = "manual_note"
    SYSTEM_ERROR        = "system_error"


class CRMActivity(BaseModel):
    id:            UUID | None = None
    lead_id:       UUID
    event_type:    ActivityType
    event_payload: dict | None = None
    actor:         str | None = None     # "system" | "user:{id}" | "webhook:sendgrid"
    trace_id:      str | None = None
    created_at:    datetime | None = None
    # No updated_at — append-only
```

---

## 2. Service Method Signatures

### LeadIngestionService

```python
class LeadIngestionService:
    async def ingest_from_csv(self, file_bytes: bytes, uploaded_by: UUID) -> IngestSummary:
        """Parse CSV, validate rows, deduplicate, persist. Returns count of created/skipped/errored."""

    async def ingest_lead(self, raw_data: dict, uploaded_by: UUID) -> Lead:
        """Validate, deduplicate, and persist a single lead. Emit LeadIngestedEvent."""

    async def get_lead(self, lead_id: UUID, requesting_user: User) -> Lead:
        """Fetch lead by ID. Enforce rep data isolation (assigned_to check)."""

    async def list_leads(self, filters: LeadFilterParams, requesting_user: User) -> Page[Lead]:
        """Paginated lead list. Rep sees only assigned; manager/admin see all."""

    async def update_status(self, lead_id: UUID, status: LeadStatus, actor: User) -> Lead:
        """Update lead status. Log state change to CRM."""
```

### InventoryMatchService

```python
class InventoryMatchService:
    async def match_lead(self, lead_id: UUID) -> MatchResult:
        """Run rule-based + pgvector match. Update lead match_status. Return matches."""

    async def get_matches_for_lead(self, lead_id: UUID) -> list[InventoryMatch]:
        """Return all inventory items matched to a lead."""

    async def update_match_rules(self, rules: MatchRuleConfig) -> None:
        """Admin-only: update the matching threshold configuration."""
```

### EnrichmentService

```python
class EnrichmentService:
    async def enrich_lead(self, lead_id: UUID) -> Contact:
        """Run Apollo → Hunter → Proxycurl cascade. Cache result. Return Contact."""

    async def _check_cache(self, domain: str) -> Contact | None:
        """Check Redis for a cached enrichment result for the given domain."""

    async def _enrich_via_apollo(self, domain: str) -> Contact | None:
        """Call Apollo.io. Return Contact or None on failure."""

    async def _enrich_via_hunter(self, domain: str) -> Contact | None:
        """Call Hunter.io fallback. Return Contact or None."""

    async def _enrich_via_proxycurl(self, linkedin_url: str) -> Contact | None:
        """Call Proxycurl for LinkedIn data. Only for high-score leads."""
```

### OutreachService

```python
class OutreachService:
    async def generate_draft(self, lead_id: UUID) -> OutreachMessage:
        """Generate AI outreach draft via LangChain agent. Save as pending_review."""

    async def approve(self, message_id: UUID, approved_by: UUID) -> OutreachMessage:
        """Approve draft. If HUMAN_REVIEW_REQUIRED=false, called automatically."""

    async def reject(self, message_id: UUID, rejected_by: UUID, reason: str) -> OutreachMessage:
        """Reject draft. Log rejection reason to CRM."""

    async def send(self, message_id: UUID) -> OutreachMessage:
        """Send approved message via SendGrid. Update status to sent."""

    async def handle_webhook(self, event: SendGridWebhookEvent) -> None:
        """Handle open/click/reply/bounce webhook. Update OutreachMessage + CRM."""
```

### CRMService

```python
class CRMService:
    async def log(
        self,
        lead_id:       UUID,
        event_type:    ActivityType,
        actor:         str,
        payload:       dict | None = None,
        trace_id:      str | None = None,
    ) -> CRMActivity:
        """Append an immutable activity record. Raises if lead_id is invalid."""

    async def get_timeline(self, lead_id: UUID) -> list[CRMActivity]:
        """Return all CRM activities for a lead, ordered by created_at ASC."""
```

---

## 3. API Request / Response Schemas

### Lead Schemas

```python
# src/api/routers/leads.py — request/response Pydantic models

class LeadCreateRequest(BaseModel):
    company_name: str
    domain:       str | None = None
    source:       str
    country:      str | None = None
    city:         str | None = None

class LeadResponse(BaseModel):
    id:           UUID
    company_name: str
    domain:       str | None
    status:       LeadStatus
    match_status: MatchStatus
    score:        float | None
    score_tier:   ScoreTier | None
    assigned_to:  UUID | None
    created_at:   datetime

class IngestSummaryResponse(BaseModel):
    created:    int
    duplicates: int
    errors:     int
    error_rows: list[dict]   # [{"row": 5, "reason": "missing company_name"}]

class LeadFilterParams(BaseModel):
    status:       LeadStatus | None = None
    match_status: MatchStatus | None = None
    score_tier:   ScoreTier | None = None
    source:       str | None = None
    assigned_to:  UUID | None = None
    page:         int = 1
    page_size:    int = 50
```

### Outreach Schemas

```python
class OutreachApproveRequest(BaseModel):
    pass  # No body required — authenticated user is the approver

class OutreachRejectRequest(BaseModel):
    reason: str  # Required for audit log

class OutreachMessageResponse(BaseModel):
    id:             UUID
    lead_id:        UUID
    contact_id:     UUID | None
    channel:        Channel
    subject:        str | None
    body:           str
    sequence_step:  int
    status:         OutreachStatus
    approved_by:    UUID | None
    sent_at:        datetime | None
    opened_at:      datetime | None
    replied_at:     datetime | None
    created_at:     datetime
```

### Standard API Response Envelope

```python
from typing import Generic, TypeVar
T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success:  bool
    data:     T | None = None
    message:  str | None = None
    trace_id: str | None = None

class PageResponse(BaseModel, Generic[T]):
    success:    bool
    data:       list[T]
    total:      int
    page:       int
    page_size:  int
    trace_id:   str | None = None
```

---

## 4. LangGraph Lead Pipeline

### State Schema

```python
# src/agents/workflows/lead_pipeline.py
from typing import TypedDict

class LeadPipelineState(TypedDict):
    lead_id:           str
    is_eligible:       bool
    contact_enriched:  bool
    lead_scored:       bool
    outreach_created:  bool
    error:             str | None
    trace_id:          str
```

### Node Definitions

```python
async def match_inventory_node(state: LeadPipelineState) -> LeadPipelineState:
    """Check inventory eligibility. Set is_eligible. Log to CRM."""
    result = await inventory_match_service.match_lead(UUID(state["lead_id"]))
    return {**state, "is_eligible": result.is_eligible}


async def enrich_contact_node(state: LeadPipelineState) -> LeadPipelineState:
    """Run Apollo→Hunter cascade. Set contact_enriched. Log to CRM."""
    try:
        await enrichment_service.enrich_lead(UUID(state["lead_id"]))
        return {**state, "contact_enriched": True}
    except IntegrationException as exc:
        logger.error("Enrichment failed", extra={"lead_id": state["lead_id"], "error": str(exc)})
        return {**state, "contact_enriched": False, "error": str(exc)}


async def score_lead_node(state: LeadPipelineState) -> LeadPipelineState:
    """Run XGBoost scoring. Set lead_scored. Log score to CRM."""
    await lead_scoring_service.score_lead(UUID(state["lead_id"]))
    return {**state, "lead_scored": True}


async def generate_outreach_node(state: LeadPipelineState) -> LeadPipelineState:
    """Generate LLM outreach draft (pending_review). Log to CRM."""
    await outreach_service.generate_draft(UUID(state["lead_id"]))
    return {**state, "outreach_created": True}


async def mark_ineligible_node(state: LeadPipelineState) -> LeadPipelineState:
    """Update lead match_status=NOT_ELIGIBLE. Log to CRM. Terminate pipeline."""
    await lead_ingestion_service.update_status(
        UUID(state["lead_id"]), MatchStatus.NOT_ELIGIBLE, actor="system"
    )
    return state
```

### Graph Definition

```python
workflow = StateGraph(LeadPipelineState)

workflow.add_node("match_inventory",   match_inventory_node)
workflow.add_node("enrich_contact",    enrich_contact_node)
workflow.add_node("score_lead",        score_lead_node)
workflow.add_node("generate_outreach", generate_outreach_node)
workflow.add_node("mark_ineligible",   mark_ineligible_node)

workflow.set_entry_point("match_inventory")

workflow.add_conditional_edges(
    "match_inventory",
    lambda s: "enrich_contact" if s["is_eligible"] else "mark_ineligible"
)
workflow.add_conditional_edges(
    "enrich_contact",
    lambda s: "score_lead" if s["contact_enriched"] else END
)
workflow.add_edge("score_lead",        "generate_outreach")
workflow.add_edge("generate_outreach", END)
workflow.add_edge("mark_ineligible",   END)

lead_pipeline = workflow.compile()
```

---

## 5. Celery Task Definitions

```python
# src/tasks/enrichment_tasks.py
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, queue="enrichment")
def enrich_lead_task(self, lead_id: str, trace_id: str) -> dict:
    """
    Enrich a single lead asynchronously.
    Retries 3x on IntegrationException (60s, 120s, 240s exponential backoff).
    """
    import asyncio
    try:
        contact = asyncio.run(enrichment_service.enrich_lead(UUID(lead_id)))
        return {"status": "success", "lead_id": lead_id, "contact_id": str(contact.id)}
    except IntegrationException as exc:
        logger.warning("Enrichment attempt failed, retrying",
                       extra={"lead_id": lead_id, "retries": self.request.retries})
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# src/tasks/outreach_tasks.py
@celery_app.task(bind=True, max_retries=2, default_retry_delay=30, queue="outreach")
def generate_outreach_task(self, lead_id: str, trace_id: str) -> dict:
    """Generate AI outreach draft for a lead. Saves as pending_review."""
    import asyncio
    try:
        message = asyncio.run(outreach_service.generate_draft(UUID(lead_id)))
        return {"status": "success", "message_id": str(message.id)}
    except Exception as exc:
        raise self.retry(exc=exc)


# src/tasks/ml_tasks.py
@celery_app.task(bind=True, max_retries=1, queue="ml")
def score_lead_task(self, lead_id: str, trace_id: str) -> dict:
    """Score a single lead using the XGBoost model."""
    import asyncio
    try:
        lead = asyncio.run(lead_scoring_service.score_lead(UUID(lead_id)))
        return {"status": "success", "lead_id": lead_id, "score": lead.score}
    except Exception as exc:
        raise self.retry(exc=exc)
```

---

## 6. LLM Prompt Design

### System Prompt (Outreach Generation)

```python
OUTREACH_SYSTEM_PROMPT = """
You are a senior sales executive at Shivam Jewels, a premium diamond wholesaler
based in India with a reputation for exceptional quality and honest trade.

Your role is to write personalised, professional outreach emails to international
jewelry buyers discovered through trade directories.

Guidelines:
- Tone: warm, knowledgeable, and concise — never salesy or pushy
- Length: 100–150 words maximum for the email body
- Always reference specific diamonds from the inventory provided (SKU, carat, shape)
- End with a single, low-pressure call to action (a call or reply to learn more)
- Do NOT mention pricing unless the inventory item has a price provided
- Do NOT invent inventory details not present in the context
- Write in English only
- Output format: JSON with keys "subject" and "body"
"""

OUTREACH_USER_PROMPT = """
Lead Company: {company_name}
Buyer Name: {buyer_name}
Buyer Title: {buyer_title}
Location: {city}, {country}

Matched Inventory:
{inventory_items}

Write a personalised outreach email for this buyer referencing the matched inventory above.
"""
```

### ML Feature Vector

| Feature | Source Table | Type | Notes |
|---|---|---|---|
| `company_country_encoded` | `leads.country` | Categorical (OHE) | Top 20 countries; rest = "other" |
| `source_type_encoded` | `leads.source` | Categorical (OHE) | gmt / trade_book / rapid_list / manual |
| `match_score_max` | `lead_inventory_matches` | Float | Max match_score across all matches |
| `match_count` | `lead_inventory_matches` | Integer | Number of inventory items matched |
| `email_verified` | `contacts.email_verified` | Boolean (0/1) | From Hunter.io |
| `has_linkedin` | `contacts.linkedin_url` | Boolean (0/1) | Profile found |
| `title_seniority` | `contacts.title` | Ordinal (0–3) | 0=unknown, 1=staff, 2=manager, 3=C-suite |
| `days_since_created` | `leads.created_at` | Integer | Lead age at scoring time |
| `carat_tier_max` | `lead_inventory_matches` | Ordinal (0–3) | Highest carat tier of matched inventory |

---

## 7. Repository Interfaces

```python
# src/repositories/base_repository.py
class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> T | None: ...
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> list[T]: ...
    @abstractmethod
    async def create(self, entity: T) -> T: ...
    @abstractmethod
    async def update(self, entity: T) -> T: ...
    @abstractmethod
    async def soft_delete(self, entity_id: UUID) -> bool: ...


# src/repositories/lead_repository.py (additional methods)
class LeadRepository(BaseRepository[Lead]):
    async def find_by_domain(self, domain: str) -> Lead | None: ...
    async def find_by_assigned_to(self, user_id: UUID, filters: LeadFilterParams) -> Page[Lead]: ...
    async def find_eligible_unscored(self, limit: int = 100) -> list[Lead]: ...
    async def update_score(self, lead_id: UUID, score: float, tier: ScoreTier) -> Lead: ...
    async def update_match_status(self, lead_id: UUID, status: MatchStatus) -> Lead: ...


# src/repositories/crm_repository.py (append-only — no update/delete)
class CRMRepository:
    async def create(self, activity: CRMActivity) -> CRMActivity: ...
    async def find_by_lead_id(self, lead_id: UUID) -> list[CRMActivity]: ...
    # NOTE: No update(), no soft_delete() — intentional
```

---

## 8. Error Response Schema

```json
{
  "success": false,
  "error": "Lead with the specified ID was not found",
  "code": "LEAD_NOT_FOUND",
  "detail": "No lead exists with ID: 3f7a1b2c-...",
  "trace_id": "req-a1b2c3d4"
}
```

### Standard Error Codes

| Code | HTTP | Trigger |
|---|---|---|
| `LEAD_NOT_FOUND` | 404 | Lead ID does not exist or is soft-deleted |
| `LEAD_VALIDATION_ERROR` | 422 | CSV row or request body failed schema validation |
| `DUPLICATE_LEAD` | 409 | Lead with same email domain already exists |
| `LEAD_NOT_ELIGIBLE` | 400 | Enrichment or outreach triggered on NOT_ELIGIBLE lead |
| `OUTREACH_PENDING_REVIEW` | 400 | Attempt to send a message not yet approved |
| `OUTREACH_ALREADY_SENT` | 409 | Attempt to send an already-sent message |
| `ENRICHMENT_ALREADY_DONE` | 400 | Re-enrichment attempted on already-enriched lead |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT token |
| `FORBIDDEN` | 403 | Valid token but insufficient role for this resource |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests — Retry-After header included |
| `INTEGRATION_ERROR` | 502 | External API (Apollo/SendGrid/OpenAI) returned an error |
| `INTERNAL_ERROR` | 500 | Unexpected server error — check trace_id in logs |

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial LLD — domain models, service signatures, API schemas, LangGraph pipeline, Celery tasks, LLM prompts, ML features, repository interfaces, error codes |
