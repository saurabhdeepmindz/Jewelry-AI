# US-039: JWT Login and Token Refresh

**Epic:** EPIC-11
**Actor:** `rep`
**Story Points:** 5
**Priority:** Critical
**Status:** Ready

## User Story

As a **rep**,
I want to log in with my username and password and receive a JWT token,
so that I can securely access the platform API without re-entering credentials on every request.

## Acceptance Criteria

### AC1: Valid login returns tokens
**Given** a user with `username=ravi`, `password=SecurePass123` exists in the DB with `is_active=true`
**When** `POST /api/v1/auth/login` is called with those credentials
**Then** 200 response with `{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}`; access token expires in 30 minutes; refresh token in 7 days

### AC2: Invalid credentials rejected
**Given** a user submits wrong password
**When** `POST /api/v1/auth/login` is called
**Then** 401 response: `{"detail": "Invalid username or password"}`; no token returned; no information about whether the username exists

### AC3: Token refresh works
**Given** a valid refresh token
**When** `POST /api/v1/auth/refresh` is called with `{"refresh_token": "..."}`
**Then** a new access token is returned; the refresh token remains valid (sliding expiry not required)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: login → access protected endpoint → refresh → access again
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Passwords hashed with bcrypt (never stored in plain text)
- [ ] `JWT_SECRET_KEY` from `Settings` — never hardcoded
- [ ] PR squash-merged to master

## Notes

- JWT payload: `{"sub": user_id, "role": role, "exp": timestamp}`
- Refresh tokens stored as hashed value in Redis (key: `refresh:{user_id}`) with TTL = 7 days
- `is_active=false` users receive 401 even with valid credentials
