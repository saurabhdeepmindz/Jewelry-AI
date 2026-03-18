"""Alembic async migration environment.

Reads DATABASE_URL from Settings so migrations use the same connection
as the application — no duplication of connection config.

Supports async migrations via asyncpg driver.
"""
import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add project root to path so `src` is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db.base import Base  # noqa: E402
from src.core.config import get_settings  # noqa: E402

# Import all models here so Alembic's autogenerate can detect them
import src.db.models  # noqa: E402, F401

config = context.config

# Configure logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at the application's metadata
target_metadata = Base.metadata

# Override sqlalchemy.url with the value from Settings
_settings = get_settings()
config.set_main_option("sqlalchemy.url", _settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL only)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations against a live async database connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (live DB) migrations."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
