from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DECIMAL, JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.ai_extraction.models.llm import ExtractionAgentModel
from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin

if TYPE_CHECKING:
    from apps.ai_extraction.models.doctype import DocTypeModel
    from apps.ai_extraction.models.fallback import FallbackChainModel, FallbackStepModel
    from apps.ai_extraction.models.llm import LLMCredentialModel, LLMModel
    from apps.ai_extraction.models.prompt_template import PromptTemplateModel
    from apps.document_intake.models.document_intake import DocumentIntakeHistory


class ExtractionAuditModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing audit logs for AI extraction operations
    """

    __tablename__ = "extraction_audit"

    request_id: Mapped[str] = mapped_column(String(36))
    external_id: Mapped[str | None] = mapped_column(String(255))
    doc_type_id: Mapped[str | None] = mapped_column(ForeignKey("doc_type.id"))
    agent_id: Mapped[str | None] = mapped_column(ForeignKey("extraction_agent.id"))
    chain_id: Mapped[str | None] = mapped_column(ForeignKey("fallback_chain.id"))
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_template.id"), nullable=True
    )
    step_seq_no: Mapped[int] = mapped_column()
    model_id: Mapped[str | None] = mapped_column(ForeignKey("llm_model.id"))
    credential_id: Mapped[str | None] = mapped_column(ForeignKey("llm_credential.id"))
    status: Mapped[str] = mapped_column(String(50))
    tokens_prompt: Mapped[int] = mapped_column()
    tokens_completion: Mapped[int] = mapped_column()
    cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 5))
    latency_ms: Mapped[int] = mapped_column()
    error_message: Mapped[str | None] = mapped_column(Text)
    step_id: Mapped[str | None] = mapped_column(ForeignKey("fallback_step.id"))
    meta_data: Mapped[dict | None] = mapped_column(JSON)

    # Document intake tracking for retry functionality
    document_intake_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_intake_history.id"), nullable=True
    )

    # Relationships
    doc_type: Mapped["DocTypeModel"] = relationship(
        "DocTypeModel", back_populates="extraction_audits"
    )

    template: Mapped["PromptTemplateModel"] = relationship(
        "PromptTemplateModel", back_populates="extraction_audits"
    )

    chain: Mapped["FallbackChainModel"] = relationship("FallbackChainModel")

    chain_step: Mapped["FallbackStepModel"] = relationship(
        "FallbackStepModel", back_populates="extraction_audits"
    )

    model: Mapped["LLMModel"] = relationship(
        "LLMModel", back_populates="extraction_audits"
    )

    credential: Mapped["LLMCredentialModel"] = relationship("LLMCredentialModel")

    agent: Mapped["ExtractionAgentModel"] = relationship("ExtractionAgentModel")

    # Relationship for document intake history
    document_intake: Mapped["DocumentIntakeHistory"] = relationship(
        "DocumentIntakeHistory", back_populates="extraction_audits"
    )

    def __repr__(self) -> str:
        """String representation of the extraction audit"""
        return f"<ExtractionAuditModel(id={self.id}, request_id={self.request_id}, status={self.status})>"
