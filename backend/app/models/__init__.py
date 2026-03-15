"""
SQLAlchemy ORM models — Base class and model imports.

All models inherit from Base so Alembic can auto-detect schema changes.
Import all models here so they are registered with Base.metadata.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class TimestampMixin:
    """Adds created_at / updated_at columns to any model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )


# Import all models so Base.metadata is fully populated for Alembic
from app.models.entry import Entry  # noqa: E402, F401
from app.models.session import Session  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
