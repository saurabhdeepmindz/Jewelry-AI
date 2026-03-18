# API Specification — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 3.5 — Architecture
**Created:** 2026-03-18
**Base URL:** `http://localhost:8000`
**Authentication:** `Authorization: Bearer <JWT>` on all endpoints except `/health` and `/auth/login`

---

## Conventions

| Convention | Rule |
|---|---|
| Versioning | All endpoints prefixed with `/api/v1/` |
| Response envelope | All responses wrap data in `{"success": true, "data": ...}` |
| Pagination | `?page=1&page_size=50`; response includes `total`, `page`, `page_size` |
| Soft deletes | `DELETE` endpoints perform soft delete (`is_deleted=true`); records remain in DB |
| Error format | `{"success": false, "error": "...", "code": "...", "detail": "...", "trace_id": "..."}` |
| Trace ID | Every response includes `X-Trace-ID` header and `trace_id` in error bodies |
| Date format | ISO 8601 UTC: `2026-03-18T09:00:00Z` |

---

## 1. Health

### `GET /health`
Check platform availability. No authentication required.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2026-03-18T09:00:00Z"
}
```

---

## 2. Authentication

### `POST /auth/login`
Exchange credentials for JWT. No authentication required.

**Request:**
```json
{
  "username": "rep_ravi",
  "password": "SecurePassword123!"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "3f7a1b2c-0001-0000-0000-000000000001",
      "username": "rep_ravi",
      "role": "rep",
      "full_name": "Ravi Sharma"
    }
  }
}
```

**Response 401:**
```json
{
  "success": false,
  "error": "Invalid username or password",
  "code": "INVALID_CREDENTIALS"
}
```

---

## 3. Leads

### `POST /api/v1/leads/upload`
Upload a CSV/Excel file of raw trade leads.

**Auth required:** `rep`, `admin`
**Content-Type:** `multipart/form-data`

**Form fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | CSV or Excel file |
| `source` | string | Yes | `gmt` \| `trade_book` \| `rapid_list` \| `manual` |

**CSV column mapping:**

| CSV Column | Field | Required |
|---|---|---|
| `company_name` | Lead.company_name | Yes |
| `domain` | Lead.domain | No |
| `email` | Used for domain extraction | No |
| `phone` | Lead.phone | No |
| `country` | Lead.country | No |
| `city` | Lead.city | No |
| `website` | Lead.website | No |

**Response 201:**
```json
{
  "success": true,
  "data": {
    "created": 18,
    "duplicates": 2,
    "errors": 1,
    "error_rows": [
      {"row": 12, "reason": "company_name is required"}
    ]
  }
}
```

---

### `GET /api/v1/leads`
List leads with filters and pagination.

**Auth required:** All roles (`rep` sees only assigned leads)

**Query parameters:**
| Param | Type | Description |
|---|---|---|
| `status` | string | Filter by LeadStatus |
| `match_status` | string | Filter by MatchStatus |
| `score_tier` | string | `high` \| `medium` \| `low` |
| `source` | string | Trade directory source |
| `assigned_to` | UUID | Filter by assigned rep (manager/admin only) |
| `page` | int | Default: 1 |
| `page_size` | int | Default: 50, max: 200 |

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "3f7a1b2c-...",
      "company_name": "Diamond World Inc.",
      "domain": "diamondworld.com",
      "country": "USA",
      "city": "New York",
      "source": "gmt",
      "status": "enriched",
      "match_status": "eligible",
      "score": 82.5,
      "score_tier": "high",
      "assigned_to": "3f7a1b2c-0001-...",
      "created_at": "2026-03-18T08:30:00Z"
    }
  ],
  "total": 143,
  "page": 1,
  "page_size": 50
}
```

---

### `GET /api/v1/leads/{lead_id}`
Get full lead detail including contacts, inventory matches, and outreach summary.

**Auth required:** All roles (rep: assigned only)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "3f7a1b2c-...",
    "company_name": "Diamond World Inc.",
    "domain": "diamondworld.com",
    "status": "contacted",
    "match_status": "eligible",
    "score": 82.5,
    "score_tier": "high",
    "contacts": [
      {
        "id": "...",
        "full_name": "John Smith",
        "title": "Head of Procurement",
        "email": "john@diamondworld.com",
        "email_verified": true,
        "phone": "+1-212-555-0100",
        "enrichment_source": "apollo"
      }
    ],
    "inventory_matches": [
      {
        "sku": "SJ-RBC-101",
        "stone_type": "RBC",
        "carat_weight": 1.02,
        "color_grade": "F",
        "clarity_grade": "VS1",
        "match_score": 0.91
      }
    ],
    "outreach_count": 2,
    "last_outreach_status": "opened",
    "created_at": "2026-03-18T08:30:00Z"
  }
}
```

---

### `PATCH /api/v1/leads/{lead_id}/status`
Manually update a lead's pipeline status.

**Auth required:** `admin`, `manager`

**Request:**
```json
{ "status": "closed" }
```

**Response 200:**
```json
{
  "success": true,
  "data": { "id": "...", "status": "closed", "updated_at": "2026-03-18T10:00:00Z" }
}
```

---

### `DELETE /api/v1/leads/{lead_id}`
Soft-delete a lead. Sets `is_deleted=true`.

**Auth required:** `admin`

**Response 200:**
```json
{ "success": true, "data": { "id": "...", "is_deleted": true } }
```

---

## 4. Inventory

### `POST /api/v1/inventory/upload`
Upload inventory from CSV/Excel.

**Auth required:** `admin`

**Response 201:**
```json
{
  "success": true,
  "data": { "created": 45, "updated": 3, "errors": 0, "error_rows": [] }
}
```

---

### `GET /api/v1/inventory`
List inventory with filters.

**Auth required:** All roles

**Query parameters:** `item_category`, `is_available`, `min_carat`, `max_carat`, `color_grade`, `page`, `page_size`

**Response 200:** Paginated list of inventory items.

---

### `PUT /api/v1/inventory/{sku}`
Update an inventory item.

**Auth required:** `admin`

**Request:**
```json
{
  "is_available": false,
  "status": "sold",
  "price_usd": 8500.00
}
```

---

### `POST /api/v1/inventory/match-rules`
Update inventory matching configuration.

**Auth required:** `admin`

**Request:**
```json
{
  "min_carat": 0.50,
  "categories": ["diamond"],
  "use_semantic_match": true,
  "semantic_threshold": 0.75
}
```

---

## 5. Enrichment

### `POST /api/v1/enrichment/{lead_id}`
Trigger contact enrichment for a single eligible lead. Returns `job_id` for polling.

**Auth required:** `rep` (assigned only), `admin`

**Response 202:**
```json
{
  "success": true,
  "data": {
    "job_id": "celery-task-uuid-...",
    "lead_id": "3f7a1b2c-...",
    "status": "queued",
    "message": "Enrichment task queued. Poll /api/v1/enrichment/status/{job_id} for result."
  }
}
```

**Response 400 (already enriched):**
```json
{
  "success": false,
  "error": "Lead is already enriched",
  "code": "ENRICHMENT_ALREADY_DONE"
}
```

---

### `POST /api/v1/enrichment/batch`
Trigger bulk enrichment for all eligible, un-enriched assigned leads.

**Auth required:** `rep`, `admin`

**Request:**
```json
{ "lead_ids": ["uuid1", "uuid2", "..."] }
```

**Response 202:**
```json
{
  "success": true,
  "data": { "queued": 12, "skipped_already_enriched": 3, "job_ids": ["..."] }
}
```

---

### `GET /api/v1/enrichment/status/{job_id}`
Poll Celery task status.

**Auth required:** `rep`, `admin`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "job_id": "...",
    "status": "SUCCESS",
    "result": { "lead_id": "...", "contact_id": "..." }
  }
}
```
`status` values: `PENDING` | `STARTED` | `SUCCESS` | `FAILURE` | `RETRY`

---

## 6. Outreach

### `POST /api/v1/outreach/generate/{lead_id}`
Generate an AI outreach draft for an enriched, eligible lead.

**Auth required:** `system` (internal), `admin`

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "msg-uuid-...",
    "lead_id": "...",
    "contact_id": "...",
    "channel": "email",
    "subject": "Exclusive RBC Diamonds for Diamond World Inc. — From Shivam Jewels",
    "body": "Dear John,\n\nI hope this message finds you well...",
    "sequence_step": 1,
    "status": "pending_review",
    "created_at": "2026-03-18T09:15:00Z"
  }
}
```

---

### `GET /api/v1/outreach/messages`
List outreach messages with filters.

**Auth required:** All roles (rep: assigned leads only)

**Query parameters:** `status`, `lead_id`, `channel`, `sequence_step`, `page`, `page_size`

---

### `PATCH /api/v1/outreach/messages/{message_id}`
Edit a draft outreach message (before approval).

**Auth required:** `manager`, `admin`

**Request:**
```json
{
  "subject": "Updated subject line",
  "body": "Updated email body..."
}
```

---

### `POST /api/v1/outreach/messages/{message_id}/approve`
Approve a pending review message. Triggers immediate send.

**Auth required:** `manager`, `admin`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "...",
    "status": "sent",
    "sent_at": "2026-03-18T09:20:00Z",
    "sendgrid_message_id": "SG.abc123..."
  }
}
```

---

### `POST /api/v1/outreach/messages/{message_id}/reject`
Reject a pending review message.

**Auth required:** `manager`, `admin`

**Request:**
```json
{ "reason": "Tone is too formal for this buyer's profile" }
```

**Response 200:**
```json
{
  "success": true,
  "data": { "id": "...", "status": "rejected", "rejection_reason": "Tone is too formal..." }
}
```

---

### `POST /api/v1/outreach/webhook`
Receive SendGrid event webhooks (open, click, reply, bounce).

**Auth:** Verified via SendGrid webhook signature header — no JWT

**Request body (SendGrid format):**
```json
[
  {
    "event": "open",
    "sg_message_id": "SG.abc123...",
    "timestamp": 1710750000,
    "email": "john@diamondworld.com"
  }
]
```

**Response 200:**
```json
{ "received": 1 }
```

---

## 7. CRM

### `GET /api/v1/crm/timeline/{lead_id}`
Full activity timeline for a lead, ordered oldest → newest.

**Auth required:** All roles (rep: own leads only; admin sees all)

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "...",
      "lead_id": "...",
      "event_type": "lead_ingested",
      "event_payload": { "source": "gmt", "batch_id": "upload-20260318" },
      "actor": "user:rep_ravi",
      "trace_id": "req-xyz789",
      "created_at": "2026-03-18T08:30:00Z"
    },
    {
      "id": "...",
      "event_type": "lead_matched",
      "event_payload": { "match_count": 3, "top_sku": "SJ-RBC-101" },
      "actor": "system",
      "created_at": "2026-03-18T08:31:05Z"
    }
  ],
  "total": 8
}
```

---

### `POST /api/v1/crm/notes/{lead_id}`
Add a manual note to a lead's CRM timeline.

**Auth required:** `rep` (own leads only), `manager`, `admin`

**Request:**
```json
{ "note": "Called John today — interested in the RBC 1.0ct range. Requested pricing." }
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "...",
    "event_type": "manual_note",
    "event_payload": { "note": "Called John today..." },
    "actor": "user:rep_ravi",
    "created_at": "2026-03-18T14:00:00Z"
  }
}
```

---

## 8. Analytics

### `GET /api/v1/analytics/funnel`
Pipeline funnel: lead counts at each status stage.

**Auth required:** `manager`, `admin`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "ingested":  320,
    "matched":   280,
    "enriched":  260,
    "scored":    260,
    "contacted": 140,
    "responded":  38,
    "closed":     12,
    "not_eligible": 40
  }
}
```

---

### `GET /api/v1/analytics/outreach-performance`
Email campaign performance metrics.

**Auth required:** `manager`, `admin`

**Query parameters:** `date_from`, `date_to`, `assigned_to`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "total_sent":    140,
    "total_opened":   82,
    "total_clicked":  34,
    "total_replied":  18,
    "total_bounced":   6,
    "open_rate":    0.586,
    "click_rate":   0.243,
    "reply_rate":   0.129,
    "bounce_rate":  0.043
  }
}
```

---

### `GET /api/v1/analytics/score-distribution`
Lead score distribution by tier.

**Auth required:** `rep`, `manager`, `admin`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "high":   { "count": 45, "percentage": 0.173 },
    "medium": { "count": 118, "percentage": 0.454 },
    "low":    { "count": 97, "percentage": 0.373 }
  }
}
```

---

## 9. Admin

### `GET /api/v1/admin/users`
List all platform users.

**Auth required:** `admin`

**Response 200:** Paginated user list (no `hashed_password` in response).

---

### `POST /api/v1/admin/users`
Create a new platform user.

**Auth required:** `admin`

**Request:**
```json
{
  "username": "rep_priya",
  "email": "priya@shivamjewels.com",
  "password": "TempPassword123!",
  "full_name": "Priya Mehta",
  "role": "rep"
}
```

---

### `PATCH /api/v1/admin/users/{user_id}`
Update user role or active status.

**Auth required:** `admin`

**Request:**
```json
{ "role": "manager", "is_active": true }
```

---

### `GET /api/v1/admin/api-keys`
List all configured API keys (masked).

**Auth required:** `admin`

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "service_name": "apollo",
      "masked_key": "sk-...****",
      "is_active": true,
      "last_rotated_at": "2026-03-01T00:00:00Z"
    }
  ]
}
```

---

### `PUT /api/v1/admin/api-keys/{service_name}`
Rotate or set an API key.

**Auth required:** `admin`

**Request:**
```json
{ "api_key": "new-apollo-api-key-value" }
```

---

### `GET /api/v1/admin/feature-flags`
List current feature flag values.

**Auth required:** `admin`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "HUMAN_REVIEW_REQUIRED": true,
    "MAX_BATCH_SIZE": 500,
    "ENRICHMENT_CACHE_TTL_DAYS": 7,
    "INVENTORY_MATCH_MIN_CARAT": 0.50
  }
}
```

---

### `PATCH /api/v1/admin/feature-flags`
Update one or more feature flags.

**Auth required:** `admin`

**Request:**
```json
{ "HUMAN_REVIEW_REQUIRED": false }
```

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial API spec — 9 resource groups, 30 endpoints, request/response schemas, error codes |
