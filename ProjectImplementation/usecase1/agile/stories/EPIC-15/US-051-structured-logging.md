# US-051: Structured JSON Logging with trace_id

**Epic:** EPIC-15
**Actor:** `system`
**Story Points:** 3
**Priority:** High
**Status:** Draft

## User Story

As the **system**,
I want every log line emitted as structured JSON with a `trace_id` correlation field,
so that engineers can trace any request or task through the entire platform by searching for one ID.

## Acceptance Criteria

### AC1: Every log line is valid JSON
**Given** the FastAPI application is running
**When** any module calls `logger.info(...)`, `logger.error(...)`, etc.
**Then** the output to stdout is a single-line valid JSON object containing at minimum: `timestamp`, `level`, `service`, `module`, `message`

### AC2: trace_id flows from HTTP request through all logs
**Given** an HTTP request arrives with `X-Trace-ID: abc-123` header
**When** the request is processed (router → service → repository) and any log lines are emitted
**Then** every log line within that request's execution contains `"trace_id": "abc-123"`

### AC3: trace_id propagated into Celery tasks
**Given** a Celery task is enqueued with `trace_id` in its arguments
**When** the task runs and emits log lines
**Then** all log lines from that task contain the same `trace_id` that originated the HTTP request

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit test: log output captured and parsed as JSON; all required keys present
- [ ] Integration test: request with `X-Trace-ID` → all logs contain the same trace_id
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- Library: `structlog` with `JSONRenderer` processor
- `trace_id` stored in `contextvars.ContextVar[str]`; populated in FastAPI middleware
- If no `X-Trace-ID` header is present → generate `uuid4()` and inject
- `X-Trace-ID` returned in every response header for client-side correlation
