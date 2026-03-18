# US-041: Admin User and API Key Management

**Epic:** EPIC-11
**Actor:** `admin`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As an **admin**,
I want to create, deactivate, and assign roles to platform users, and manage encrypted API keys,
so that I can onboard new team members and rotate external service credentials without touching the codebase.

## Acceptance Criteria

### AC1: Admin creates a new user
**Given** an admin calls `POST /api/v1/admin/users` with `{"username": "priya", "email": "priya@shivam.com", "password": "TempPass!", "role": "manager"}`
**When** the request is processed
**Then** a new `User` row is created with `hashed_password` (never plain text); `is_active=true`; the user can immediately log in

### AC2: Admin deactivates a user
**Given** an admin calls `PATCH /api/v1/admin/users/{id}` with `{"is_active": false}`
**When** the update is applied
**Then** `users.is_active = false`; all subsequent login attempts by that user return 401; existing tokens are invalidated (Redis refresh token deleted)

### AC3: Admin stores encrypted API key
**Given** an admin calls `POST /api/v1/admin/api-keys` with `{"service_name": "apollo", "api_key": "plaintext_key"}`
**When** the request is processed
**Then** the key is encrypted with Fernet before storage; `api_key_configs.encrypted_key` contains the ciphertext; the plain-text key is never logged or returned

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: create user → login → deactivate → login fails
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Security review: no plain-text passwords or keys in logs or responses
- [ ] PR squash-merged to master

## Notes

- Fernet key: `Settings.FERNET_ENCRYPTION_KEY` — never hardcoded
- `POST /api/v1/admin/api-keys` response does NOT return the decrypted key — only `service_name`, `is_active`, `last_rotated_at`
- Only `ROLE_ADMIN` can access `/api/v1/admin/` routes
