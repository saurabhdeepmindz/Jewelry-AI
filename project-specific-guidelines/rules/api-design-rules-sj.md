# API Design Rules

## URL Conventions

- Lowercase, hyphenated: `/api/v1/lead-matches`
- Nouns, not verbs: `/api/v1/leads` not `/api/v1/getLeads`
- Version prefix: always `/api/v1/`
- Nested resources only one level deep: `/api/v1/leads/{id}/contacts`

## HTTP Methods

| Operation | Method | Notes |
|---|---|---|
| Read list | GET | Paginated |
| Read single | GET | Returns 404 if not found |
| Create | POST | Returns 201 + created resource |
| Full update | PUT | Idempotent |
| Partial update | PATCH | Only changed fields |
| Delete | DELETE | Soft delete; returns 204 |

## Response Format

All responses use this envelope:

```json
// Success
{"success": true, "data": {...}, "meta": {"total": 100, "page": 1, "limit": 20}}

// Error
{"success": false, "error": "Human-readable message", "code": "LEAD_NOT_FOUND", "trace_id": "req-xyz"}
```

## Status Codes

- `200` — OK
- `201` — Created
- `204` — No Content (delete)
- `400` — Bad Request (validation error)
- `401` — Unauthorized
- `403` — Forbidden
- `404` — Not Found
- `422` — Unprocessable Entity (Pydantic validation)
- `429` — Too Many Requests
- `500` — Internal Server Error

## Pagination

All list endpoints support: `?page=1&limit=20&sort=created_at&order=desc`

## Naming

- Request bodies: `XxxCreateRequest`, `XxxUpdateRequest`
- Response bodies: `XxxResponse`, `XxxListResponse`
