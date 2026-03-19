"""Unit test fixtures.

Unit tests mock all external dependencies (DB, Redis, HTTP).
The async_client here does NOT require a real database.
"""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """FastAPI test client for unit tests — no real DB needed."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
