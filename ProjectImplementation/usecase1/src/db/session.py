"""Async SQLAlchemy engine and session factory.

Architecture.md §7 — Database Session Management.

The engine is module-level (created once at import time).
`get_async_session` is an async generator used as a FastAPI dependency.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(
    _settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,        # Discard stale connections before use
    echo=_settings.APP_ENV == "development",
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Keep ORM objects usable after commit
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a DB session and auto-commits / rolls back."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
