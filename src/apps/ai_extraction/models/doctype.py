from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin

if TYPE_CHECKING:
    from apps.ai_extraction.models.extraction_audit import ExtractionAuditModel
    from apps.ai_extraction.models.llm import ExtractionAgentModel
    from apps.ai_extraction.models.prompt_template import PromptTemplateModel


class DocTypeModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing different document types for AI processing
    """

    __tablename__ = "doc_type"

    code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Relationships - Using 'all' cascade without delete-orphan for soft delete support
    prompt_templates: Mapped[List["PromptTemplateModel"]] = relationship(
        "PromptTemplateModel", back_populates="doc_type", cascade="all"
    )

    extraction_audits: Mapped[List["ExtractionAuditModel"]] = relationship(
        "ExtractionAuditModel", back_populates="doc_type"
    )

    extraction_agents: Mapped[List["ExtractionAgentModel"]] = relationship(
        "ExtractionAgentModel", back_populates="doc_type"
    )

    document_intakes: Mapped[List["DocumentIntakeHistory"]] = relationship(
        "DocumentIntakeHistory", back_populates="doc_type"
    )

    def __repr__(self) -> str:
        """String representation of the document type"""
        return f"<DocTypeModel(id={self.id}, code={self.code})>"
