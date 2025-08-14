from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import DECIMAL, TIMESTAMP, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin

if TYPE_CHECKING:
    from apps.ai_extraction.models.doctype import DocTypeModel
    from apps.ai_extraction.models.extraction_audit import ExtractionAuditModel


class PromptTemplateModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing prompt templates for different document types
    """

    __tablename__ = "prompt_template"

    doc_type_id: Mapped[str] = mapped_column(ForeignKey("doc_type.id"))
    version: Mapped[int] = mapped_column()
    language: Mapped[str] = mapped_column(String(10), default="en")
    temperature: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), default=Decimal("0.0"))
    top_p: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), default=Decimal("1.0"))
    max_tokens: Mapped[int] = mapped_column(default=1024)
    template_body: Mapped[str] = mapped_column(Text)

    # Relationships
    doc_type: Mapped["DocTypeModel"] = relationship(
        "DocTypeModel", back_populates="prompt_templates"
    )

    extraction_audits: Mapped[List["ExtractionAuditModel"]] = relationship(
        "ExtractionAuditModel", back_populates="template"
    )

    def __repr__(self) -> str:
        """String representation of the prompt template"""
        return f"<PromptTemplateModel(id={self.id}, doc_type_id={self.doc_type_id}, version={self.version})>"
