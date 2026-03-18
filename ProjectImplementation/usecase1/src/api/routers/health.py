"""Health check endpoints.

US-052 — Health Check and Readiness Probe Endpoints.

GET /health       — Liveness probe. Always 200. No external checks. < 5ms.
GET /health/ready — Readiness probe. Checks DB (SELECT 1) and Redis (PING).
                    200 when healthy; 503 when any dependency is down.

Both endpoints are exempt from JWT auth and rate limiting.
"""
import time

import redis.asyncio as aioredis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.core.config import get_settings
from src.core.logging import get_logger
from src.db.session import AsyncSessionLocal

router = APIRouter(tags=["health"])
logger = get_logger(__name__)
_settings = get_settings()


@router.get("/health", response_model=None)
async def liveness() -> dict[str, str]:
    """Liveness probe — returns 200 while the process is alive.

    No database or Redis checks are performed.
    Safe to call at any frequency from container orchestration.
    """
    return {
        "status": "ok",
        "service": "jewelry-ai",
        "version": _settings.APP_VERSION,
    }


@router.get("/health/ready", response_model=None)
async def readiness() -> JSONResponse:
    """Readiness probe — checks PostgreSQL and Redis reachability.

    Returns 200 when all dependencies healthy; 503 when any are down.
    FastAPI process continues running even when 503 is returned.
    """
    checks: dict[str, str] = {}
    checks_ms: dict[str, int] = {}
    overall_status = 200

    # ── PostgreSQL check ─────────────────────────────────────────────────────
    t0 = time.monotonic()
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc}"
        overall_status = 503
        logger.error("Readiness check: DB unreachable: %s", exc)
    checks_ms["db"] = round((time.monotonic() - t0) * 1000)

    # ── Redis check ──────────────────────────────────────────────────────────
    t1 = time.monotonic()
    try:
        r = aioredis.from_url(_settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        overall_status = 503
        logger.error("Readiness check: Redis unreachable: %s", exc)
    checks_ms["redis"] = round((time.monotonic() - t1) * 1000)

    body = {
        "status": "ready" if overall_status == 200 else "not_ready",
        **checks,
        "checks_ms": checks_ms,
    }
    return JSONResponse(content=body, status_code=overall_status)
