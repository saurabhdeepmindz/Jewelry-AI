# US-040: Role-Based Endpoint Authorization

**Epic:** EPIC-11
**Actor:** `system`
**Story Points:** 5
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want every protected endpoint to enforce role-based access control,
so that reps, managers, and admins can only perform actions permitted for their role.

## Acceptance Criteria

### AC1: Request without token returns 401
**Given** any protected endpoint (all except `/health` and `/auth/login`)
**When** called without an `Authorization: Bearer {token}` header
**Then** 401 response: `{"detail": "Not authenticated"}`

### AC2: Wrong role returns 403
**Given** a rep calls `PATCH /api/v1/outreach/messages/{id}/approve` (manager/admin only)
**When** the `require_role("manager", "admin")` dependency evaluates
**Then** 403 response: `{"detail": "Insufficient role. Required: manager, admin"}`

### AC3: Rep data isolation enforced
**Given** a rep calls `GET /api/v1/leads` with a valid JWT
**When** `LeadRepository.list_for_user()` is called
**Then** only leads where `assigned_to = current_user.id` are returned; leads assigned to other reps are never included

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests: all role/endpoint combinations in RBAC matrix tested
- [ ] Integration test: rep → manager endpoint → 403
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- `get_current_user` dependency: decodes JWT, loads user from DB, verifies `is_active=true`
- `require_role(*roles)` is a FastAPI dependency factory: `Depends(require_role("manager", "admin"))`
- Rep data isolation is enforced at the **repository layer** — not in the router — to prevent accidental bypass
- Expired token returns 401 (not 403); wrong role returns 403
