# Database Schema — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 3.4 — Architecture
**Created:** 2026-03-18
**Database:** PostgreSQL 16+ with pgvector 0.7+ extension

---

## Conventions

| Convention | Rule |
|---|---|
| Primary key | `UUID` generated with `gen_random_uuid()` — never integer sequences |
| Soft deletes | `is_deleted BOOLEAN NOT NULL DEFAULT false` — no hard `DELETE` on domain tables |
| Timestamps | `created_at` and `updated_at` are `TIMESTAMPTZ NOT NULL DEFAULT NOW()` on all tables |
| Enums | Defined as `VARCHAR` with application-level validation — avoids costly `ALTER TYPE` in migrations |
| Foreign keys | All `_id` columns reference parent table explicitly |
| Naming | `snake_case` for all tables and columns |
| Append-only | `crm_activity` has no `updated_at` — it is never updated |

---

## Enum Reference

### LeadStatus
```
ingested → matched → enriched → scored → contacted → responded → closed
```

### MatchStatus
```
pending → eligible | not_eligible
```

### ContactSource
```
apollo | hunter | proxycurl | manual
```

### OutreachStatus
```
draft → pending_review → approved → sent → opened → clicked → replied | bounced | rejected
```

### Channel
```
email | whatsapp | linkedin
```

### ActivityType
```
lead_ingested | lead_matched | lead_not_eligible | lead_enriched | lead_scored
outreach_drafted | outreach_approved | outreach_rejected | outreach_sent
email_opened | email_clicked | email_replied | email_bounced
whatsapp_sent | whatsapp_replied | manual_note | system_error
```

### ItemCategory
```
diamond | ruby | sapphire | emerald | other_gemstone | jewelry
```

### ItemStatus
```
available | reserved | sold | inactive
```

---

## Table Definitions

### Table: `leads`

Core entity. One record per unique buyer company (deduplicated by email domain).

```sql
CREATE TABLE leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name    VARCHAR(255) NOT NULL,
    domain          VARCHAR(255),                   -- email domain for deduplication
    country         VARCHAR(100),
    state           VARCHAR(100),
    city            VARCHAR(100),
    phone           VARCHAR(50),
    website         VARCHAR(255),
    source          VARCHAR(100) NOT NULL,           -- gmt | trade_book | rapid_list | manual | api
    status          VARCHAR(50)  NOT NULL DEFAULT 'ingested',
                                                    -- ingested | matched | enriched | scored
                                                    -- contacted | responded | closed
    match_status    VARCHAR(50)  NOT NULL DEFAULT 'pending',
                                                    -- pending | eligible | not_eligible
    score           FLOAT,                          -- 0.0–100.0 from XGBoost model (NULL until scored)
    score_tier      VARCHAR(20),                    -- high | medium | low (derived from score)
    embedding       VECTOR(1536),                   -- pgvector: OpenAI text-embedding-3-small
    assigned_to     UUID REFERENCES users(id),      -- NULL = unassigned
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID REFERENCES users(id)
);

CREATE INDEX idx_leads_status        ON leads(status)        WHERE is_deleted = false;
CREATE INDEX idx_leads_match_status  ON leads(match_status)  WHERE is_deleted = false;
CREATE INDEX idx_leads_score         ON leads(score DESC)    WHERE is_deleted = false;
CREATE INDEX idx_leads_assigned_to   ON leads(assigned_to)   WHERE is_deleted = false;
CREATE INDEX idx_leads_source        ON leads(source)        WHERE is_deleted = false;
CREATE UNIQUE INDEX idx_leads_domain ON leads(domain)        WHERE is_deleted = false AND domain IS NOT NULL;
```

---

### Table: `inventory`

Shivam Jewels' diamond and jewelry stock. Source of truth for matching.

```sql
CREATE TABLE inventory (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             VARCHAR(100) UNIQUE NOT NULL,
    item_category   VARCHAR(50) NOT NULL,           -- diamond | ruby | sapphire | jewelry | etc.
    stone_type      VARCHAR(50),                    -- RBC | princess | oval | cushion | emerald_cut
    shape           VARCHAR(50),
    carat_weight    DECIMAL(6,2) NOT NULL,           -- GIA standard: 2 decimal places always
    color_grade     VARCHAR(10),                    -- D | E | F | G | H | I | J ...
    clarity_grade   VARCHAR(10),                    -- IF | VVS1 | VVS2 | VS1 | VS2 | SI1 | SI2
    cut_grade       VARCHAR(20),                    -- Excellent | Very Good | Good | Fair
    certification   VARCHAR(50),                    -- GIA | IGI | HRD | AGS
    cert_number     VARCHAR(100),
    price_usd       DECIMAL(12,2),
    status          VARCHAR(20) NOT NULL DEFAULT 'available',
                                                    -- available | reserved | sold | inactive
    is_available    BOOLEAN NOT NULL DEFAULT true,  -- fast filter for matching
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inventory_category   ON inventory(item_category) WHERE is_deleted = false;
CREATE INDEX idx_inventory_available  ON inventory(is_available)  WHERE is_deleted = false;
CREATE INDEX idx_inventory_carat      ON inventory(carat_weight)  WHERE is_deleted = false;
```

---

### Table: `lead_inventory_matches`

Association between a lead and the inventory items it matched.

```sql
CREATE TABLE lead_inventory_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    inventory_id    UUID NOT NULL REFERENCES inventory(id),
    match_score     FLOAT NOT NULL,                -- 0.0–1.0: rule-based match quality
    match_reason    JSONB,                         -- {"stone_type": true, "carat_range": true, ...}
    match_method    VARCHAR(20) NOT NULL DEFAULT 'rule',  -- rule | embedding | hybrid
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_matches_lead_id      ON lead_inventory_matches(lead_id);
CREATE INDEX idx_matches_inventory_id ON lead_inventory_matches(inventory_id);
CREATE UNIQUE INDEX idx_matches_lead_inventory
    ON lead_inventory_matches(lead_id, inventory_id);
```

---

### Table: `contacts`

Enriched buyer contacts at lead companies. Multiple contacts per lead are allowed.

```sql
CREATE TABLE contacts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id             UUID NOT NULL REFERENCES leads(id),
    full_name           VARCHAR(255),
    title               VARCHAR(255),
    email               VARCHAR(255),
    email_verified      BOOLEAN DEFAULT false,
    phone               VARCHAR(50),
    linkedin_url        VARCHAR(500),
    enrichment_source   VARCHAR(50),               -- apollo | hunter | proxycurl | manual
    enriched_at         TIMESTAMPTZ,
    is_deleted          BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contacts_lead_id ON contacts(lead_id)
    WHERE is_deleted = false;
CREATE UNIQUE INDEX idx_contacts_lead_email ON contacts(lead_id, email)
    WHERE is_deleted = false AND email IS NOT NULL;
```

---

### Table: `outreach_messages`

AI-generated email and WhatsApp drafts with full lifecycle tracking.

```sql
CREATE TABLE outreach_messages (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id                 UUID NOT NULL REFERENCES leads(id),
    contact_id              UUID REFERENCES contacts(id),
    channel                 VARCHAR(20) NOT NULL DEFAULT 'email',  -- email | whatsapp | linkedin
    subject                 VARCHAR(500),
    body                    TEXT NOT NULL,
    sequence_step           INTEGER NOT NULL DEFAULT 1,            -- 1=initial, 2=day4, 3=day7
    status                  VARCHAR(30) NOT NULL DEFAULT 'draft',
                                                    -- draft | pending_review | approved
                                                    -- sent | opened | clicked | replied
                                                    -- bounced | rejected
    rejection_reason        TEXT,                  -- set when status=rejected
    approved_by             UUID REFERENCES users(id),
    approved_at             TIMESTAMPTZ,
    sendgrid_message_id     VARCHAR(255),           -- set after send
    sent_at                 TIMESTAMPTZ,
    opened_at               TIMESTAMPTZ,
    clicked_at              TIMESTAMPTZ,
    replied_at              TIMESTAMPTZ,
    bounced_at              TIMESTAMPTZ,
    is_deleted              BOOLEAN NOT NULL DEFAULT false,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_outreach_lead_id    ON outreach_messages(lead_id)    WHERE is_deleted = false;
CREATE INDEX idx_outreach_status     ON outreach_messages(status)     WHERE is_deleted = false;
CREATE INDEX idx_outreach_contact_id ON outreach_messages(contact_id) WHERE is_deleted = false;
```

---

### Table: `crm_activity`

**Append-only.** Immutable audit trail — no `UPDATE` or `DELETE` ever executed on this table.

```sql
CREATE TABLE crm_activity (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    event_type      VARCHAR(100) NOT NULL,
                                -- lead_ingested | lead_matched | lead_not_eligible
                                -- lead_enriched | lead_scored | outreach_drafted
                                -- outreach_approved | outreach_rejected | outreach_sent
                                -- email_opened | email_clicked | email_replied | email_bounced
                                -- manual_note | system_error
    event_payload   JSONB,      -- flexible: {"score": 82, "tier": "high"} or {"note": "Called today"}
    actor           VARCHAR(100),  -- system | user:{user_id} | agent:outreach | webhook:sendgrid
    trace_id        VARCHAR(100),  -- correlation ID from the originating HTTP request or task
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- NOTE: No updated_at — this table is append-only, immutable by design
);

CREATE INDEX idx_crm_lead_id     ON crm_activity(lead_id);
CREATE INDEX idx_crm_event_type  ON crm_activity(event_type);
CREATE INDEX idx_crm_created_at  ON crm_activity(created_at DESC);
```

---

### Table: `users`

Platform users with authentication credentials and role assignments.

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(100) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255),
    role            VARCHAR(50) NOT NULL DEFAULT 'rep',
                                -- admin | manager | rep | system
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_login_at   TIMESTAMPTZ,
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID REFERENCES users(id)
);

CREATE UNIQUE INDEX idx_users_username ON users(username) WHERE is_deleted = false;
CREATE UNIQUE INDEX idx_users_email    ON users(email)    WHERE is_deleted = false;
```

---

### Table: `api_key_configs`

Encrypted external API keys managed by admin. Keys are never stored in plain text.

```sql
CREATE TABLE api_key_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name    VARCHAR(100) UNIQUE NOT NULL,  -- apollo | hunter | proxycurl | sendgrid | openai
    encrypted_key   TEXT NOT NULL,                 -- Fernet-encrypted; decrypted only in memory
    description     VARCHAR(255),
    last_rotated_at TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by      UUID REFERENCES users(id)
);
```

---

## Migration Index

| Migration | Description | Phase |
|---|---|---|
| `001_baseline.py` | Empty baseline — establishes migration history | Phase 0 |
| `002_create_leads_inventory.py` | `leads`, `inventory` tables + pgvector extension | Phase 1 |
| `003_create_matches_contacts.py` | `lead_inventory_matches`, `contacts` tables | Phase 1 |
| `004_create_outreach_crm.py` | `outreach_messages`, `crm_activity` tables | Phase 1–2 |
| `005_create_users_api_keys.py` | `users`, `api_key_configs` tables | Phase 2 |
| `006_add_score_fields_to_leads.py` | `score`, `score_tier` columns on `leads` | Phase 2 |
| `007_add_embedding_to_leads.py` | `embedding VECTOR(1536)` column + IVFFlat index | Phase 1 |

---

## pgvector Index

```sql
-- Applied in migration 007
-- IVFFlat: good performance up to ~1M vectors; tune lists = sqrt(row_count)
CREATE INDEX idx_leads_embedding ON leads
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

**Usage in matching:**
```sql
-- Find top 10 inventory items semantically similar to a lead's embedding
SELECT i.id, i.sku, i.carat_weight, i.stone_type,
       l.embedding <=> i.embedding AS distance
FROM leads l
JOIN inventory i ON true
WHERE l.id = :lead_id
  AND i.is_available = true
ORDER BY distance ASC
LIMIT 10;
```

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial schema — 7 tables, enums, indexes, pgvector, migration index |
