# API Specification — Jewelry AI Platform

**Base URL:** `/api/v1`
**Auth:** `Authorization: Bearer <accessToken>`
**Content-Type:** `application/json`

---

## Standard Response Envelope

Every API response returns exactly one of these three shapes. No exceptions.

### Success
```json
{ "success": true, "message": "Optional human-readable message", "data": { } }
```

### Paginated
```json
{
  "success": true,
  "data": [ ],
  "meta": { "total": 100, "page": 1, "limit": 20, "last_page": 5 }
}
```

### Error
```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "trace_id": "req-uuid-here",
  "detail": null
}
```

### Validation Error (422)
```json
{
  "success": false,
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "trace_id": "req-uuid-here",
  "detail": [
    { "field": "company_name", "message": "field required" },
    { "field": "source", "message": "value is not a valid enum member" }
  ]
}
```

---

## Authentication — `/api/v1/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | Public | Login with email + password, receive JWT |
| POST | `/auth/logout` | JWT | Invalidate current session |
| POST | `/auth/refresh` | Refresh JWT | Obtain new access token |
| GET | `/auth/me` | JWT | Get current user profile |
| POST | `/auth/change-password` | JWT | Change own password |

### POST `/auth/login`

**Request:**
```json
{ "email": "admin@shivamjewels.com", "password": "SecurePass123!" }
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "user": { "id": "uuid-here", "email": "admin@shivamjewels.com", "role": "admin" },
    "access_token": "<jwt>",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Response 401:**
```json
{ "success": false, "error": "Invalid credentials", "code": "INVALID_CREDENTIALS", "trace_id": "..." }
```

---

## Leads — `/api/v1/leads`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/leads/upload` | JWT | Upload CSV/Excel lead file |
| GET | `/leads` | JWT | List leads (paginated, filterable) |
| GET | `/leads/{lead_id}` | JWT | Get full lead detail |
| PATCH | `/leads/{lead_id}/status` | JWT | Update lead status manually |
| DELETE | `/leads/{lead_id}` | JWT | Soft-delete a lead |
| GET | `/leads/{lead_id}/timeline` | JWT | Full CRM activity timeline for lead |
| GET | `/leads/{lead_id}/matches` | JWT | Inventory matches for lead |

### POST `/leads/upload`

**Request:** `multipart/form-data`
```
file: <CSV or Excel file>
source: "gmt" | "trade_book" | "rapid_list" | "manual"
```

**Response 201:**
```json
{
  "success": true,
  "message": "Upload processed",
  "data": {
    "job_id": "celery-task-uuid",
    "total_rows": 150,
    "accepted": 142,
    "rejected": 5,
    "duplicates": 3,
    "rejected_rows": [
      { "row": 14, "reason": "Missing company_name" },
      { "row": 37, "reason": "Invalid email format" }
    ]
  }
}
```

### GET `/leads`

**Query Parameters:**
```
page=1&limit=20
status=ingested|matched|enriched|contacted|responded|closed
match_status=pending|eligible|not_eligible
source=gmt|trade_book|rapid_list|manual
min_score=50
max_score=100
search=diamond
sort_by=score|created_at|company_name
sort_order=asc|desc
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "company_name": "Pristine Diamonds LLC",
      "domain": "pristinediamonds.com",
      "country": "USA",
      "city": "New York",
      "source": "gmt",
      "status": "enriched",
      "match_status": "eligible",
      "score": 87.4,
      "contact": {
        "name": "Sarah Mitchell",
        "title": "Head Buyer",
        "email": "s.mitchell@pristinediamonds.com",
        "email_verified": true
      },
      "matched_inventory_count": 3,
      "created_at": "2026-03-17T10:00:00Z"
    }
  ],
  "meta": { "total": 348, "page": 1, "limit": 20, "last_page": 18 }
}
```

### GET `/leads/{lead_id}`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "company_name": "Pristine Diamonds LLC",
    "domain": "pristinediamonds.com",
    "country": "USA",
    "state": "New York",
    "city": "New York",
    "phone": "+1-212-555-0100",
    "source": "gmt",
    "status": "contacted",
    "match_status": "eligible",
    "score": 87.4,
    "contact": {
      "id": "uuid",
      "name": "Sarah Mitchell",
      "title": "Head Buyer",
      "email": "s.mitchell@pristinediamonds.com",
      "phone": "+1-212-555-0101",
      "linkedin_url": "https://linkedin.com/in/sarahmitchell",
      "email_verified": true,
      "enrichment_source": "apollo"
    },
    "inventory_matches": [
      {
        "sku": "DIA-RBC-1.02-D-IF",
        "shape": "RBC",
        "carat_weight": 1.02,
        "color_grade": "D",
        "clarity_grade": "IF",
        "cut_grade": "Excellent",
        "certification": "GIA",
        "price_usd": 8500.00,
        "match_score": 0.95
      }
    ],
    "outreach_messages": [
      {
        "id": "uuid",
        "channel": "email",
        "subject": "Exclusive RBC Diamonds — Crafted for Premium Buyers",
        "status": "opened",
        "sequence_step": 1,
        "sent_at": "2026-03-17T14:00:00Z",
        "opened_at": "2026-03-17T15:30:00Z"
      }
    ],
    "created_at": "2026-03-17T10:00:00Z",
    "updated_at": "2026-03-17T14:00:00Z"
  }
}
```

### PATCH `/leads/{lead_id}/status`

**Request:**
```json
{ "status": "closed", "note": "Not interested — budget constraints" }
```

**Response 200:**
```json
{ "success": true, "data": { "id": "uuid", "status": "closed" } }
```

---

## Inventory — `/api/v1/inventory`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/inventory/upload` | JWT | Upload inventory CSV/Excel |
| GET | `/inventory` | JWT | List inventory (filterable) |
| GET | `/inventory/{sku}` | JWT | Get single inventory item |
| PUT | `/inventory/{sku}` | JWT | Update inventory item |
| DELETE | `/inventory/{sku}` | JWT | Mark item as unavailable |
| GET | `/inventory/match-rules` | JWT | Get current match rules config |
| PUT | `/inventory/match-rules` | JWT | Update match rules |

### GET `/inventory`

**Query Parameters:**
```
shape=RBC|princess|oval|cushion|emerald
min_carat=0.5&max_carat=3.0
color_grade=D|E|F|G|H
clarity_grade=IF|VVS1|VVS2|VS1|VS2
certification=GIA|IGI|HRD
is_available=true|false
page=1&limit=50
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "sku": "DIA-RBC-1.02-D-IF",
      "stone_type": "diamond",
      "shape": "RBC",
      "carat_weight": 1.02,
      "color_grade": "D",
      "clarity_grade": "IF",
      "cut_grade": "Excellent",
      "certification": "GIA",
      "cert_number": "2456789123",
      "price_usd": 8500.00,
      "is_available": true
    }
  ],
  "meta": { "total": 245, "page": 1, "limit": 50, "last_page": 5 }
}
```

### PUT `/inventory/match-rules`

**Request:**
```json
{
  "min_carat": 0.50,
  "max_carat": 5.00,
  "allowed_shapes": ["RBC", "princess", "oval"],
  "allowed_certifications": ["GIA", "IGI"],
  "min_color_grade": "H",
  "min_clarity_grade": "VS2"
}
```

**Response 200:**
```json
{ "success": true, "message": "Match rules updated", "data": { ... } }
```

---

## Enrichment — `/api/v1/enrichment`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/enrichment/{lead_id}` | JWT | Trigger enrichment for single lead |
| POST | `/enrichment/batch` | JWT | Enqueue bulk enrichment job |
| GET | `/enrichment/jobs/{job_id}` | JWT | Poll Celery job status |

### POST `/enrichment/{lead_id}`

**Response 202:**
```json
{
  "success": true,
  "message": "Enrichment job queued",
  "data": {
    "job_id": "celery-task-uuid",
    "lead_id": "lead-uuid",
    "status": "queued",
    "estimated_completion_seconds": 15
  }
}
```

### GET `/enrichment/jobs/{job_id}`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "job_id": "celery-task-uuid",
    "status": "completed",
    "result": {
      "lead_id": "uuid",
      "contact_id": "contact-uuid",
      "enrichment_source": "apollo",
      "email_verified": true
    }
  }
}
```

Job statuses: `queued` | `in_progress` | `completed` | `failed` | `retrying`

---

## Outreach — `/api/v1/outreach`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/outreach/generate/{lead_id}` | JWT | Generate AI outreach draft |
| GET | `/outreach/messages` | JWT | List all outreach messages |
| GET | `/outreach/messages/{message_id}` | JWT | Get single message |
| PATCH | `/outreach/messages/{message_id}` | JWT | Edit draft before sending |
| POST | `/outreach/messages/{message_id}/send` | JWT | Send approved message |
| POST | `/outreach/messages/{message_id}/cancel` | JWT | Cancel scheduled message |

### POST `/outreach/generate/{lead_id}`

**Request (optional overrides):**
```json
{
  "tone": "formal" | "friendly" | "concise",
  "include_inventory_skus": ["DIA-RBC-1.02-D-IF"],
  "sequence_step": 1
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "message_id": "uuid",
    "channel": "email",
    "subject": "Exclusive RBC Diamonds for Pristine Diamonds LLC",
    "body": "Dear Sarah,\n\nI hope this message finds you well...",
    "status": "draft",
    "requires_review": true,
    "sequence_step": 1,
    "generated_by": "gpt-4o",
    "token_count": 312
  }
}
```

### PATCH `/outreach/messages/{message_id}`

**Request:**
```json
{
  "subject": "Updated subject line",
  "body": "Updated email body..."
}
```

### POST `/outreach/messages/{message_id}/send`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "message_id": "uuid",
    "status": "sent",
    "sendgrid_message_id": "sg-msg-id",
    "sent_at": "2026-03-17T14:00:00Z"
  }
}
```

---

## CRM & Analytics — `/api/v1/crm`, `/api/v1/analytics`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/crm/timeline/{lead_id}` | JWT | Full activity timeline for lead |
| GET | `/crm/tasks` | JWT | Open follow-up tasks |
| PATCH | `/crm/tasks/{task_id}` | JWT | Update task status |
| GET | `/analytics/funnel` | JWT | Pipeline funnel metrics |
| GET | `/analytics/outreach-performance` | JWT | Email open/reply/click metrics |
| GET | `/analytics/lead-sources` | JWT | Lead source quality comparison |
| GET | `/analytics/inventory-match-distribution` | JWT | Match distribution by cut/carat |

### GET `/crm/timeline/{lead_id}`

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "event_type": "lead_ingested",
      "message": "Lead ingested from GMT source",
      "agent": "system",
      "created_at": "2026-03-17T10:00:00Z"
    },
    {
      "id": "uuid",
      "event_type": "inventory_matched",
      "message": "Matched 3 inventory items — marked ELIGIBLE",
      "agent": "system",
      "created_at": "2026-03-17T10:01:00Z"
    },
    {
      "id": "uuid",
      "event_type": "contact_enriched",
      "message": "Contact enriched via Apollo.io",
      "agent": "system",
      "created_at": "2026-03-17T10:02:30Z"
    },
    {
      "id": "uuid",
      "event_type": "email_sent",
      "message": "Outreach email sent — step 1",
      "agent": "system",
      "created_at": "2026-03-17T14:00:00Z"
    }
  ]
}
```

### GET `/analytics/funnel`

**Query Parameters:** `date_from=2026-01-01&date_to=2026-03-17&source=gmt`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "period": { "from": "2026-01-01", "to": "2026-03-17" },
    "funnel": [
      { "stage": "ingested", "count": 1250, "percentage": 100 },
      { "stage": "matched_eligible", "count": 687, "percentage": 55 },
      { "stage": "enriched", "count": 598, "percentage": 47.8 },
      { "stage": "contacted", "count": 502, "percentage": 40.2 },
      { "stage": "responded", "count": 89, "percentage": 7.1 },
      { "stage": "closed", "count": 24, "percentage": 1.9 }
    ]
  }
}
```

---

## System — `/api/v1/system`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | Public | Health check (load balancer / uptime monitoring) |
| GET | `/system/config` | JWT Admin | Current feature flag + match rule config |

### GET `/health`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "timestamp": "2026-03-17T10:00:00Z",
    "version": "1.0.0",
    "db": "connected",
    "redis": "connected"
  }
}
```

---

## Common Query Parameters (All List Endpoints)

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Records per page (max 100) |
| `sort_by` | string | `created_at` | Field to sort by |
| `sort_order` | string | `desc` | `asc` or `desc` |
| `search` | string | — | Full-text search on key fields |

---

## HTTP Status Code Reference

| Code | When Used |
|---|---|
| 200 | Successful GET, PATCH, DELETE |
| 201 | Successful POST creating a resource |
| 202 | Accepted — async job queued |
| 204 | No content (DELETE) |
| 400 | Bad request, malformed payload |
| 401 | Missing or invalid JWT |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | Conflict — duplicate |
| 422 | Pydantic validation failure |
| 429 | Rate limit exceeded |
| 500 | Unhandled server error |

---

## Swagger / OpenAPI

Available at `http://localhost:8000/docs` (development only).
Disabled when `APP_ENV=production`.

All FastAPI routers MUST have:
- `tags=["Domain Name"]` on the router
- `summary=` on each endpoint
- `response_model=` typed response on each endpoint
- Request body documented via Pydantic schema
