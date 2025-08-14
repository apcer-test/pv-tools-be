from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.ai_extraction.models.doctype import DocTypeModel
from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin

if TYPE_CHECKING:
    from apps.ai_extraction.models.extraction_audit import ExtractionAuditModel


class DocumentIntakeStatus(PyEnum):
    """Generic status enum for tracking workflows"""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentIntakeSource(PyEnum):
    """Source of document intake"""

    USER_UPLOAD = "USER_UPLOAD"
    SYSTEM_UPLOAD = "SYSTEM_UPLOAD"


class DocumentIntakeHistory(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Document intake history table - tracks all document intake requests
    """

    __tablename__ = "document_intake_history"

    # Core fields
    status: Mapped[DocumentIntakeStatus] = mapped_column(
        Enum(DocumentIntakeStatus), default=DocumentIntakeStatus.PENDING
    )
    source: Mapped[DocumentIntakeSource] = mapped_column(
        Enum(DocumentIntakeSource), default=DocumentIntakeSource.USER_UPLOAD
    )
    email_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column(Integer)
    doc_type_id: Mapped[str] = mapped_column(ForeignKey("doc_type.id"))

    # Request tracking
    request_id: Mapped[str] = mapped_column(String(26), index=True)  # ULID as string

    # Processing metadata
    processing_started_at: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # ISO timestamp
    processing_completed_at: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # ISO timestamp
    error_message: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(100))
    failed_at_step: Mapped[str | None] = mapped_column(String(100))

    # Metadata
    meta_data: Mapped[dict | None] = mapped_column(JSON)

    # Relationships
    doc_type: Mapped["DocTypeModel"] = relationship(
        "DocTypeModel", back_populates="document_intakes"
    )

    # Relationship for extraction audits
    # extraction_audits: Mapped[List["ExtractionAuditModel"]] = relationship(
    #     "ExtractionAuditModel",
    #     back_populates="document_intake",
    #     cascade="all, delete-orphan",
    # )

    def __repr__(self) -> str:
        """String representation of the document intake history"""
        return f"<DocumentIntakeHistory(id={self.id}, request_id={self.request_id}, status={self.status})>"
