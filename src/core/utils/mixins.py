import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID


class TimeStampMixin:
    """
    A mixin class to add automatic timestamp fields and audit fields.

    Adds `created_at`, `updated_at`, `deleted_at` fields and audit fields
    `created_by`, `updated_by`, `deleted_by` to a model.
    """

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        default=None, server_default=None
    )


class UserMixin:
    """
    A mixin class to add audit fields for tracking who created, updated, and deleted records.

    Adds `created_by`, `updated_by`, `deleted_by` fields that reference user UUIDs.
    This mixin should be used in combination with TimeStampMixin for complete audit trail.
    """

    # Audit fields - these will reference user UUIDs
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment="User ID who created this record"
    )
    updated_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="User ID who last updated this record",
    )
    deleted_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="User ID who soft deleted this record",
    )


class UUIDPrimaryKeyMixin:
    """
    A mixin class to add a UUID primary key field in a model.
    """

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, nullable=False
    )


class ULIDPrimaryKeyMixin:
    """
    A mixin class to add a ULID primary key field in a model.
    ULID is stored as string in database but supports proper ULID operations.
    """

    id: Mapped[str] = mapped_column(
        primary_key=True, default=lambda: str(ULID()), nullable=False
    )
