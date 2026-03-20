# Database Schema — Jewelry AI Platform

**ORM:** SQLAlchemy 2.x (async)
**Query Builder:** SQLAlchemy Core
**Database:** PostgreSQL 16+
**Extension:** pgvector 0.7+
**Convention:** `snake_case` columns in DB ↔ `snake_case` in Python (no mapping needed)

---

## Schema Conventions

### Required on Every Table

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key — `gen_random_uuid()` default. Always UUID (never integer). |
| `created_at` | `TIMESTAMPTZ` | Set on insert, `DEFAULT NOW()` |
| `updated_at` | `TIMESTAMPTZ` | Set on insert, updated by application layer |
| `is_deleted` | `BOOLEAN` | Soft delete. `DEFAULT false`. Hard deletes forbidden. |

### Naming Rules
- All column names: `snake_case`
- Boolean columns: `is_<state>` (e.g., `is_available`, `is_deleted`, `is_verified`)
- Status/type columns: `VARCHAR(50)` with Python `Enum` — never magic integers
- Foreign keys: `<table_singular>_id` (e.g., `lead_id`, `contact_id`); always indexed
- JSONB columns: only for non-queryable metadata (`meta`, `event_payload`)
- Audit trail: `created_at`, `updated_at`, `created_by` on all mutable entities

---

## Core Domain Tables

### `leads`

Primary entity. One row per company/buyer prospect.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | |
| `company_name` | VARCHAR(255) | NOT NULL | |
| `domain` | VARCHAR(255) | nullable | Company website domain |
| `country` | VARCHAR(100) | nullable | |
| `state` | VARCHAR(100) | nullable | |
| `city` | VARCHAR(100) | nullable | |
| `phone` | VARCHAR(50) | nullable | |
| `website` | VARCHAR(255) | nullable | |
| `source` | VARCHAR(100) | NOT NULL | See `LeadSource` enum |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'ingested' | See `LeadStatus` enum |
| `match_status` | VARCHAR(50) | DEFAULT 'pending' | See `MatchStatus` enum |
| `score` | FLOAT | nullable | 0.0–100.0 from ML model |
| `embedding` | VECTOR(1536) | nullable | pgvector — semantic dedup |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT false | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `created_by` | VARCHAR(100) | nullable | user UUID or "system" |

**Indexes:**
```sql
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_match_status ON leads(match_status);
CREATE INDEX idx_leads_score ON leads(score DESC NULLS LAST);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_company_name ON leads(company_name);
CREATE INDEX idx_leads_is_deleted ON leads(is_deleted);
-- pgvector approximate nearest-neighbor index for semantic dedup
CREATE INDEX idx_leads_embedding ON leads USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

### `inventory`

Shivam Jewels' diamond and jewelry stock.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | |
| `sku` | VARCHAR(100) | UNIQUE, NOT NULL | Human-readable identifier |
| `stone_type` | VARCHAR(50) | NOT NULL | `diamond`, `sapphire`, `ruby`, `emerald` |
| `shape` | VARCHAR(50) | NOT NULL | See `DiamondShape` enum |
| `carat_weight` | DECIMAL(6,2) | NOT NULL | |
| `color_grade` | VARCHAR(10) | nullable | D, E, F, G, H, I, J ... |
| `clarity_grade` | VARCHAR(10) | nullable | IF, VVS1, VVS2, VS1, VS2, SI1, SI2 |
| `cut_grade` | VARCHAR(20) | nullable | Excellent, Very Good, Good, Fair |
| `certification` | VARCHAR(50) | nullable | GIA, IGI, HRD |
| `cert_number` | VARCHAR(100) | nullable, UNIQUE | |
| `price_usd` | DECIMAL(12,2) | nullable | |
| `is_available` | BOOLEAN | NOT NULL, DEFAULT true | |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT false | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes:**
```sql
CREATE INDEX idx_inventory_shape ON inventory(shape);
CREATE INDEX idx_inventory_carat ON inventory(carat_weight);
CREATE INDEX idx_inventory_is_available ON inventory(is_available);
CREATE INDEX idx_inventory_stone_type ON inventory(stone_type);
CREATE INDEX idx_inventory_color ON inventory(color_grade);
CREATE INDEX idx_inventory_clarity ON inventory(clarity_grade);
```

---

### `lead_inventory_matches`

Join table recording which inventory items matched which leads.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `lead_id` | UUID | NOT NULL, FK → leads.id, index | |
| `inventory_id` | UUID | NOT NULL, FK → inventory.id, index | |
| `match_score` | FLOAT | NOT NULL | 0.0–1.0 quality of rule match |
| `match_reason` | JSONB | nullable | Which rules matched and how |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes:**
```sql
CREATE INDEX idx_matches_lead_id ON lead_inventory_matches(lead_id);
CREATE INDEX idx_matches_inventory_id ON lead_inventory_matches(inventory_id);
CREATE UNIQUE INDEX idx_matches_lead_inventory ON lead_inventory_matches(lead_id, inventory_id);
```

---

### `contacts`

Enriched buyer contact details linked to a lead.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `lead_id` | UUID | NOT NULL, FK → leads.id, index | |
| `full_name` | VARCHAR(255) | nullable | |
| `title` | VARCHAR(255) | nullable | e.g., Head Buyer, Procurement Manager |
| `email` | VARCHAR(255) | nullable | |
| `email_verified` | BOOLEAN | DEFAULT false | Hunter.io verification |
| `phone` | VARCHAR(50) | nullable | |
| `linkedin_url` | VARCHAR(500) | nullable | |
| `enrichment_source` | VARCHAR(50) | nullable | `apollo`, `hunter`, `linkedin`, `manual` |
| `enriched_at` | TIMESTAMPTZ | nullable | |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT false | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes:**
```sql
CREATE INDEX idx_contacts_lead_id ON contacts(lead_id);
CREATE UNIQUE INDEX idx_contacts_lead_email ON contacts(lead_id, email);
```

---

### `outreach_messages`

Every AI-generated or manual outreach message per lead/contact.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `lead_id` | UUID | NOT NULL, FK → leads.id, index | |
| `contact_id` | UUID | nullable, FK → contacts.id | |
| `channel` | VARCHAR(50) | NOT NULL | `email`, `whatsapp`, `linkedin` |
| `subject` | VARCHAR(500) | nullable | Email subject only |
| `body` | TEXT | NOT NULL | |
| `sequence_step` | INTEGER | NOT NULL, DEFAULT 1 | Step 1, 2, 3 in sequence |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'draft' | See `MessageStatus` enum |
| `generated_by` | VARCHAR(100) | nullable | LLM model used (e.g., `gpt-4o`) |
| `token_count` | INTEGER | nullable | Tokens used in generation |
| `sendgrid_message_id` | VARCHAR(255) | nullable | For open/click tracking |
| `sent_at` | TIMESTAMPTZ | nullable | |
| `opened_at` | TIMESTAMPTZ | nullable | |
| `clicked_at` | TIMESTAMPTZ | nullable | |
| `replied_at` | TIMESTAMPTZ | nullable | |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT false | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes:**
```sql
CREATE INDEX idx_outreach_lead_id ON outreach_messages(lead_id);
CREATE INDEX idx_outreach_status ON outreach_messages(status);
CREATE INDEX idx_outreach_channel ON outreach_messages(channel);
```

---

### `crm_activity`

Immutable audit log of every pipeline event per lead.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `lead_id` | UUID | NOT NULL, FK → leads.id, index | |
| `event_type` | VARCHAR(100) | NOT NULL | See `CRMEventType` enum |
| `message` | TEXT | nullable | Human-readable summary |
| `event_payload` | JSONB | nullable | Full event data |
| `agent` | VARCHAR(100) | nullable | `system`, `user:{uuid}`, `agent:enrichment` |
| `trace_id` | VARCHAR(100) | nullable | Request correlation ID |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | **Never updated — audit log** |

**No `is_deleted` or `updated_at`** — CRM activity is append-only and immutable.

**Indexes:**
```sql
CREATE INDEX idx_crm_lead_id ON crm_activity(lead_id);
CREATE INDEX idx_crm_event_type ON crm_activity(event_type);
CREATE INDEX idx_crm_created_at ON crm_activity(created_at DESC);
```

---

### `inventory_match_rules`

Configurable rules used by the inventory match engine.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `rule_name` | VARCHAR(100) | NOT NULL | e.g., `default`, `premium_buyers` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | |
| `min_carat` | DECIMAL(6,2) | nullable | |
| `max_carat` | DECIMAL(6,2) | nullable | |
| `allowed_shapes` | TEXT[] | nullable | PostgreSQL array |
| `allowed_certifications` | TEXT[] | nullable | |
| `min_color_grade` | VARCHAR(10) | nullable | |
| `min_clarity_grade` | VARCHAR(10) | nullable | |
| `min_cut_grade` | VARCHAR(20) | nullable | |
| `config` | JSONB | nullable | Additional rule parameters |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

### `users`

Platform users (sales reps, managers, admins).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | |
| `password_hash` | VARCHAR | NOT NULL | bcrypt, rounds=12 |
| `full_name` | VARCHAR(255) | nullable | |
| `role` | VARCHAR(50) | NOT NULL, DEFAULT 'rep' | `admin`, `manager`, `rep` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | |
| `last_login_at` | TIMESTAMPTZ | nullable | Used to invalidate old JWTs |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT false | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

## Enums Reference

Document every Python `Enum` used in the schema so intent is never ambiguous.

### `LeadStatus` (leads.status)
| Value | Description |
|---|---|
| `ingested` | Lead received, not yet processed |
| `matched` | Inventory matching completed |
| `enriched` | Contact enrichment completed |
| `contacted` | At least one outreach sent |
| `responded` | Lead has replied |
| `closed` | Deal won, lost, or no longer active |

### `MatchStatus` (leads.match_status)
| Value | Description |
|---|---|
| `pending` | Not yet matched |
| `eligible` | Matched — qualifies for outreach |
| `not_eligible` | No inventory match found |

### `LeadSource` (leads.source)
| Value | Description |
|---|---|
| `gmt` | GMT trade directory |
| `trade_book` | Jewelry Book of Trade |
| `rapid_list` | Rapid API scraped list |
| `hill_list` | Hill List source |
| `manual` | Manually added |

### `MessageStatus` (outreach_messages.status)
| Value | Description |
|---|---|
| `draft` | AI-generated, not yet reviewed |
| `pending_review` | Submitted for human review |
| `approved` | Approved, queued for sending |
| `sent` | Successfully delivered |
| `opened` | Recipient opened email |
| `clicked` | Recipient clicked a link |
| `replied` | Recipient replied |
| `bounced` | Delivery failed |
| `cancelled` | Cancelled before send |

### `CRMEventType` (crm_activity.event_type)
| Value | Description |
|---|---|
| `lead_ingested` | Lead added to system |
| `lead_duplicated` | Duplicate detected, skipped |
| `inventory_matched` | Match result recorded |
| `contact_enriched` | Enrichment completed |
| `enrichment_failed` | Enrichment attempt failed |
| `score_computed` | ML score assigned |
| `email_draft_created` | Outreach draft generated |
| `email_approved` | Draft approved for send |
| `email_sent` | Email delivered |
| `email_opened` | Email opened |
| `email_clicked` | Link clicked |
| `reply_received` | Buyer replied |
| `status_changed` | Lead status manually updated |

### `DiamondShape` (inventory.shape)
| Value |
|---|
| `RBC` (Round Brilliant Cut) |
| `princess` |
| `oval` |
| `cushion` |
| `emerald` |
| `asscher` |
| `marquise` |
| `radiant` |
| `pear` |
| `heart` |

---

## Migration Files Index

Maintain this index as migrations are added to `src/db/migrations/versions/`.

```
src/db/migrations/versions/
├── 001_create_users.py
├── 002_create_inventory.py
├── 003_create_leads.py
├── 004_create_contacts.py
├── 005_create_lead_inventory_matches.py
├── 006_create_outreach_messages.py
├── 007_create_crm_activity.py
├── 008_create_inventory_match_rules.py
└── 009_add_pgvector_extension.py
```

**Migration rules:**
- Each migration must have an `upgrade()` and `downgrade()` function
- Test `downgrade()` locally before PR
- Never delete or modify an applied migration — create a new one to fix it
- Run `alembic upgrade head` in deployment startup script

---

## SQLAlchemy Model Template

```python
# src/db/models/lead.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Float, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from src.db.base import Base


class LeadModel(Base):
    """SQLAlchemy ORM model for the leads table."""

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    source = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="ingested", index=True)
    match_status = Column(String(50), default="pending", index=True)
    score = Column(Float, nullable=True, index=True)
    embedding = Column(Vector(1536), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), nullable=False)
```
