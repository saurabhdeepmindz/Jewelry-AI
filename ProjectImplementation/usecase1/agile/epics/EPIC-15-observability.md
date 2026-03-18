# EPIC-15: Observability, Monitoring & Alerting

**Status:** Draft
**Phase:** Phase 4
**Layer(s):** Layer 6 — Reporting
**Priority:** Medium
**Estimated Size:** M

---

## Problem Statement

In production, silent failures are the most dangerous: an enrichment Celery task that crashes without logging, a scoring model that starts returning all `low` scores, a SendGrid API key that quietly expires. Without structured logging, health endpoints, and metrics dashboards, the team is flying blind.

## Goal

Every service emits structured JSON logs with `trace_id` correlation. Health check endpoints expose service liveness and readiness. A Prometheus + Grafana stack visualizes pipeline throughput, error rates, Celery queue depths, and external API latency — with alerts on critical thresholds.

## Scope (In)

- Structured JSON logging via `structlog` with `trace_id`, `level`, `timestamp`, `service`, `module`
- `X-Trace-ID` request header propagation: generate UUID4 per request; flow through all logs and CRM activity
- `GET /api/v1/health` — liveness probe (always returns 200 if process is up)
- `GET /api/v1/health/ready` — readiness probe (checks DB connection, Redis ping)
- Prometheus metrics via `prometheus-fastapi-instrumentator`:
  - HTTP request count / latency by route and status code
  - Celery task success/failure rates per queue
  - External API call latency by provider
  - Active lead counts by status and score_tier
- Grafana dashboards: pipeline throughput, error rate, Celery queue depth, lead funnel
- Alertmanager rules: error rate > 5% for 5 minutes; Celery `ml` queue depth > 100; DB pool exhaustion
- Prometheus + Grafana + Alertmanager in Docker Compose

## Scope (Out)

- Distributed tracing with Jaeger or Zipkin (structured logs with trace_id are sufficient for Phase 4)
- Log aggregation with Elasticsearch / Kibana (Docker log driver + file logs are sufficient)
- PagerDuty / OpsGenie integration (Alertmanager email alerts are sufficient for Phase 4)

---

## Acceptance Criteria

- [ ] AC1: Every log line contains: `trace_id`, `level`, `timestamp` (ISO 8601), `service=jewelry-ai`, `module`
- [ ] AC2: `GET /health` returns 200 in < 5ms regardless of DB state
- [ ] AC3: `GET /health/ready` returns 200 when DB and Redis are reachable; returns 503 when either is down
- [ ] AC4: Grafana dashboard shows real-time Celery task success/failure counts per queue
- [ ] AC5: Alertmanager fires an email alert when error rate exceeds 5% for 5 consecutive minutes in staging
- [ ] AC6: A failing Celery task produces a log line with `level=ERROR`, `trace_id`, `task_name`, and `error` keys — confirmed in log output

---

## User Stories

- US-051: Structured JSON logging with trace_id — `agile/stories/EPIC-15/US-051-structured-logging.md`
- US-052: Health check and readiness probe endpoints — `agile/stories/EPIC-15/US-052-health-endpoints.md`
- US-053: Prometheus metrics and Grafana dashboard — `agile/stories/EPIC-15/US-053-prometheus-grafana.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| Prometheus (self-hosted) | Metrics scraping | None (internal Docker network) |
| Grafana (self-hosted) | Dashboards + alerts | `GF_SECURITY_ADMIN_PASSWORD` |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Grafana dashboard JSON committed to `src/monitoring/grafana/`
- [ ] Alertmanager rules file committed to `src/monitoring/alertmanager/`
- [ ] Health endpoints tested with DB down (503 confirmed)
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
