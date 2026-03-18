"""Redis-backed job status store for async task tracking.

Keys: job:{job_id} → JSON blob, TTL 24 hours.
"""
import json
from datetime import timedelta

import redis.asyncio as aioredis

from src.core.config import get_settings

_JOB_TTL = timedelta(hours=24)
_KEY_PREFIX = "job:"


def _redis() -> aioredis.Redis:  # type: ignore[type-arg]
    return aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)


async def set_job_status(job_id: str, data: dict) -> None:  # type: ignore[type-arg]
    """Persist job status to Redis with 24-hour TTL."""
    r = _redis()
    try:
        await r.setex(
            f"{_KEY_PREFIX}{job_id}",
            int(_JOB_TTL.total_seconds()),
            json.dumps(data),
        )
    finally:
        await r.aclose()


async def get_job_status(job_id: str) -> dict | None:  # type: ignore[type-arg]
    """Retrieve job status from Redis; returns None if not found."""
    r = _redis()
    try:
        raw = await r.get(f"{_KEY_PREFIX}{job_id}")
        if raw is None:
            return None
        return json.loads(raw)  # type: ignore[no-any-return]
    finally:
        await r.aclose()
