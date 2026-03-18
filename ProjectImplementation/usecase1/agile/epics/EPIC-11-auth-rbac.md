# EPIC-11: Authentication & Role-Based Access

**Status:** Ready
**Phase:** Phase 2
**Layer(s):** Layer 1 — Core Data (users, api_key_configs)
**Priority:** Critical
**Estimated Size:** M

---

## Problem Statement

Without authentication, all API endpoints are open to anyone. Without role-based access control, a sales rep can approve their own outreach drafts, view other reps' leads, or access admin configuration. These are unacceptable security and compliance gaps before any external deployment.

## Goal

All API endpoints require a valid JWT token. Role-based permissions are enforced at the route level — reps see only their assigned leads, managers can approve outreach, and only admins can manage users and API key configuration. Token refresh extends sessions without re-login.

## Scope (In)

- `POST /api/v1/auth/login` — username + password → access token + refresh token
- `POST /api/v1/auth/refresh` — refresh token → new access token
- `POST /api/v1/auth/logout` — invalidate refresh token
- JWT with 30-minute access token TTL; 7-day refresh token TTL
- `get_current_user` FastAPI dependency injected into all protected routes
- `require_role(*roles)` dependency for route-level RBAC
- Rep data isolation: `LeadRepository` filters `assigned_to = current_user.id` for `ROLE_REP`
- Admin user management: `GET/POST /api/v1/admin/users`, `PATCH /api/v1/admin/users/{id}`
- Password hashing: `bcrypt` via `passlib`
- Admin API key management: `GET/POST/DELETE /api/v1/admin/api-keys` — encrypted storage

## Scope (Out)

- OAuth2 / SSO (SAML, Google login) — Phase 4 if needed
- MFA / 2FA
- Session management beyond JWT TTL
- API key rate limiting (EPIC-14)

---

## Acceptance Criteria

- [ ] AC1: Valid credentials → 200 with `access_token` and `refresh_token`; invalid credentials → 401
- [ ] AC2: All non-health endpoints return 401 without a valid JWT in `Authorization: Bearer {token}`
- [ ] AC3: `ROLE_REP` calling `GET /api/v1/leads` sees only leads where `assigned_to = their user_id`
- [ ] AC4: `ROLE_REP` calling `PATCH .../approve` → 403 Forbidden
- [ ] AC5: Expired access token + valid refresh token → `POST /api/v1/auth/refresh` returns new access token
- [ ] AC6: Admin creates a user via `POST /api/v1/admin/users` → user can immediately log in with the provided password

---

## User Stories

- US-039: JWT login and token refresh — `agile/stories/EPIC-11/US-039-jwt-auth.md`
- US-040: Role-based endpoint authorization — `agile/stories/EPIC-11/US-040-rbac-middleware.md`
- US-041: Admin user and API key management — `agile/stories/EPIC-11/US-041-admin-user-management.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| None | Auth is internal; API keys managed in DB | — |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Security review: no secrets in code, no plain-text passwords in DB
- [ ] RBAC matrix tested: all role/endpoint combinations verified
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
