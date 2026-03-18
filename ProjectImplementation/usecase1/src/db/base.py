"""SQLAlchemy declarative base for all ORM models.

All ORM models must inherit from Base so Alembic can detect them
for autogenerate migrations.

Import pattern in alembic/env.py:
    from src.db.base import Base
    import src.db.models  # noqa: F401 — registers all models with Base.metadata
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass
