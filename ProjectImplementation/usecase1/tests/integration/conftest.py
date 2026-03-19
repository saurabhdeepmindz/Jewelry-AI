"""Integration test fixtures.

Integration tests require running PostgreSQL and Redis containers.
Run with: pytest tests/integration/ -v -m integration

The db_session fixture creates all tables, yields a session that auto-rolls
back after each test, then drops all tables — full isolation per test.
"""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import all models to register them with Base.metadata
import src.db.models  # noqa: F401
from src.core.config import get_settings
from src.db.base import Base
from src.db.session import get_async_session
from src.main import app


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a test engine against the test database."""
    settings = get_settings()
    test_url = settings.TEST_DATABASE_URL or settings.DATABASE_URL
    assert "test" in test_url.lower() or "pytest" in test_url.lower(), (
        f"Integration tests must use a TEST database. Got: {test_url}\n"
        "Set TEST_DATABASE_URL to a dedicated test database."
    )
    engine = create_async_engine(test_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    """Yield a DB session that rolls back all changes after each test."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncClient:
    """FastAPI test client wired to the test DB session."""
    app.dependency_overrides[get_async_session] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()
