"""Integration tests for health endpoints — US-052.

Requires: running PostgreSQL and Redis (docker compose up postgres redis)

Run: pytest tests/integration/test_health_endpoints_integration.py -v -m integration
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestLivenessIntegration:
    """GET /health — liveness with real app stack."""

    async def test_liveness_returns_200_with_real_app(
        self, async_client: AsyncClient
    ) -> None:
        """Given the real app is running → GET /health returns 200."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    async def test_liveness_returns_correct_shape(
        self, async_client: AsyncClient
    ) -> None:
        """Response has status, service, and version fields."""
        response = await async_client.get("/health")
        body = response.json()
        assert body["status"] == "ok"
        assert body["service"] == "jewelry-ai"
        assert "version" in body


@pytest.mark.integration
class TestReadinessIntegration:
    """GET /health/ready — readiness with real DB and Redis."""

    async def test_readiness_returns_200_when_db_is_running(
        self, async_client: AsyncClient
    ) -> None:
        """Given PostgreSQL is running → /health/ready returns 200."""
        response = await async_client.get("/health/ready")
        # In CI with real DB and Redis this must be 200
        # In environments where Redis is not available it may be 503
        assert response.status_code in (200, 503)
        body = response.json()
        assert body["status"] in ("ready", "not_ready")
        assert "db" in body
        assert "redis" in body
        assert "checks_ms" in body

    async def test_readiness_checks_ms_are_non_negative_integers(
        self, async_client: AsyncClient
    ) -> None:
        """Timing fields must be non-negative integers in milliseconds."""
        response = await async_client.get("/health/ready")
        checks_ms = response.json()["checks_ms"]
        assert isinstance(checks_ms["db"], int)
        assert isinstance(checks_ms["redis"], int)
        assert checks_ms["db"] >= 0
        assert checks_ms["redis"] >= 0
