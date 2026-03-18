"""Unit tests for src/api/routers/health.py — US-052.

TDD: Health endpoints must meet exact AC1-AC3 from the user story.
Run: pytest tests/unit/api/test_health_router.py -v
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestLivenessProbe:
    """/health — always returns 200; never checks external dependencies."""

    async def test_liveness_returns_200(self, async_client: AsyncClient) -> None:
        """AC1: GET /health returns 200."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    async def test_liveness_response_has_status_ok(self, async_client: AsyncClient) -> None:
        """AC1: response body contains status=ok."""
        response = await async_client.get("/health")
        assert response.json()["status"] == "ok"

    async def test_liveness_response_has_service_name(self, async_client: AsyncClient) -> None:
        """AC1: response body contains service=jewelry-ai."""
        response = await async_client.get("/health")
        assert response.json()["service"] == "jewelry-ai"

    async def test_liveness_response_has_version_field(self, async_client: AsyncClient) -> None:
        """AC1: response body contains version field."""
        response = await async_client.get("/health")
        assert "version" in response.json()

    async def test_liveness_does_not_call_db(self, async_client: AsyncClient) -> None:
        """AC1: /health must not perform any DB check."""
        with patch("src.api.routers.health.AsyncSessionLocal") as mock_session:
            await async_client.get("/health")
            mock_session.assert_not_called()

    async def test_liveness_does_not_call_redis(self, async_client: AsyncClient) -> None:
        """AC1: /health must not perform any Redis check."""
        with patch("src.api.routers.health.aioredis") as mock_redis:
            await async_client.get("/health")
            mock_redis.from_url.assert_not_called()


class TestReadinessProbe:
    """/health/ready — 200 when healthy; 503 when dependency is down."""

    def _mock_healthy_db(self) -> tuple[MagicMock, MagicMock]:
        """Return context manager mocks for a healthy DB session."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=None)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        return mock_session, mock_cm

    def _mock_healthy_redis(self) -> MagicMock:
        """Return a mock for a healthy Redis connection."""
        mock_r = AsyncMock()
        mock_r.ping = AsyncMock(return_value=True)
        mock_r.aclose = AsyncMock()
        return mock_r

    async def test_readiness_returns_200_when_all_healthy(
        self, async_client: AsyncClient
    ) -> None:
        """AC2: Returns 200 when DB and Redis are reachable."""
        _, mock_cm = self._mock_healthy_db()
        mock_redis = self._mock_healthy_redis()

        with (
            patch("src.api.routers.health.AsyncSessionLocal", return_value=mock_cm),
            patch("src.api.routers.health.aioredis.from_url", return_value=mock_redis),
        ):
            response = await async_client.get("/health/ready")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["db"] == "ok"
        assert body["redis"] == "ok"

    async def test_readiness_response_includes_checks_ms(
        self, async_client: AsyncClient
    ) -> None:
        """AC2: Response includes checks_ms with db and redis timings."""
        _, mock_cm = self._mock_healthy_db()
        mock_redis = self._mock_healthy_redis()

        with (
            patch("src.api.routers.health.AsyncSessionLocal", return_value=mock_cm),
            patch("src.api.routers.health.aioredis.from_url", return_value=mock_redis),
        ):
            response = await async_client.get("/health/ready")

        checks_ms = response.json()["checks_ms"]
        assert "db" in checks_ms
        assert "redis" in checks_ms
        assert isinstance(checks_ms["db"], int)
        assert isinstance(checks_ms["redis"], int)

    async def test_readiness_returns_503_when_db_down(
        self, async_client: AsyncClient
    ) -> None:
        """AC3: Returns 503 with db=error when PostgreSQL is unreachable."""
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=Exception("connection refused"))
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_redis = self._mock_healthy_redis()

        with (
            patch("src.api.routers.health.AsyncSessionLocal", return_value=mock_cm),
            patch("src.api.routers.health.aioredis.from_url", return_value=mock_redis),
        ):
            response = await async_client.get("/health/ready")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "not_ready"
        assert "error" in body["db"]
        assert body["redis"] == "ok"

    async def test_readiness_returns_503_when_redis_down(
        self, async_client: AsyncClient
    ) -> None:
        """AC3 variant: Returns 503 when Redis is unreachable."""
        _, mock_cm = self._mock_healthy_db()
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("redis connection refused"))
        mock_redis.aclose = AsyncMock()

        with (
            patch("src.api.routers.health.AsyncSessionLocal", return_value=mock_cm),
            patch("src.api.routers.health.aioredis.from_url", return_value=mock_redis),
        ):
            response = await async_client.get("/health/ready")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "not_ready"
        assert body["db"] == "ok"
        assert "error" in body["redis"]

    async def test_readiness_process_continues_when_503(
        self, async_client: AsyncClient
    ) -> None:
        """AC3: FastAPI process does not crash when DB is down — subsequent requests work."""
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=Exception("DB down"))
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_redis = self._mock_healthy_redis()

        with (
            patch("src.api.routers.health.AsyncSessionLocal", return_value=mock_cm),
            patch("src.api.routers.health.aioredis.from_url", return_value=mock_redis),
        ):
            # First call — DB down
            r1 = await async_client.get("/health/ready")
            assert r1.status_code == 503

            # Second call — liveness still works (process is up)
            r2 = await async_client.get("/health")
            assert r2.status_code == 200


class TestTraceIDHeader:
    """/health and /health/ready must propagate X-Trace-ID."""

    async def test_health_returns_trace_id_header(self, async_client: AsyncClient) -> None:
        """Given X-Trace-ID in request → same ID returned in response header."""
        response = await async_client.get(
            "/health", headers={"X-Trace-ID": "my-trace-abc"}
        )
        assert response.headers.get("X-Trace-ID") == "my-trace-abc"

    async def test_health_generates_trace_id_when_absent(self, async_client: AsyncClient) -> None:
        """Given no X-Trace-ID header → a UUID4 is generated and returned."""
        response = await async_client.get("/health")
        trace_id = response.headers.get("X-Trace-ID")
        assert trace_id is not None
        assert len(trace_id) == 36  # UUID4 format
