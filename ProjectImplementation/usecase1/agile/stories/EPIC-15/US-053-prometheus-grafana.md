# US-053: Prometheus Metrics and Grafana Dashboard

**Epic:** EPIC-15
**Actor:** `admin`
**Story Points:** 8
**Priority:** Medium
**Status:** Draft

## User Story

As an **admin**,
I want Prometheus metrics collected from FastAPI and Celery, visualized in a Grafana dashboard,
so that the team can see pipeline throughput and error rates at a glance and be alerted to problems.

## Acceptance Criteria

### AC1: Prometheus scrapes FastAPI metrics
**Given** `prometheus-fastapi-instrumentator` is installed and configured
**When** `GET /metrics` is called by Prometheus
**Then** all HTTP request count, latency (p50/p95/p99), and error rate metrics are exposed in Prometheus text format; Prometheus UI shows them as active targets

### AC2: Grafana dashboard shows key panels
**Given** Grafana is connected to Prometheus and the dashboard JSON is imported
**When** an admin opens the Jewelry AI dashboard
**Then** it shows: HTTP request rate, p95 latency, error rate (5xx), Celery task success/failure per queue, lead funnel counts by status

### AC3: Alertmanager fires email on high error rate
**Given** the error rate (5xx responses / total requests) exceeds 5% for 5 consecutive minutes
**When** Alertmanager evaluates the alert rule
**Then** an email alert is sent to the configured recipient; the alert resolves automatically when error rate drops below 5%

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Prometheus, Grafana, Alertmanager added to `docker-compose.yml`
- [ ] Grafana dashboard JSON committed to `src/monitoring/grafana/jewelry-ai-dashboard.json`
- [ ] Alertmanager rules committed to `src/monitoring/alertmanager/rules.yml`
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Alert tested: simulated 5xx errors → alert fires in staging
- [ ] No hardcoded secrets — `GF_SECURITY_ADMIN_PASSWORD` from env
- [ ] PR squash-merged to master

## Notes

- Grafana provisioning via `docker-compose.yml` volume mount (no manual dashboard import)
- Celery metrics via `celery-prometheus-exporter` sidecar or custom task signals
- `GET /metrics` endpoint should be rate-limited or restricted to internal network only in production
- Prometheus scrape interval: `15s` for FastAPI; `30s` for Celery exporter
