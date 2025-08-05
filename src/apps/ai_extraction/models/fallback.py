from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import DECIMAL, JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin

if TYPE_CHECKING:
    from apps.ai_extraction.models.extraction_audit import ExtractionAuditModel
    from apps.ai_extraction.models.llm import LLMCredentialModel, LLMModel


class FallbackChainModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing fallback chains for AI model redundancy
    """

    __tablename__ = "fallback_chain"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    max_total_retries: Mapped[int] = mapped_column(default=3)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships - Using 'all' cascade without delete-orphan, with ordering
    fallback_steps: Mapped[List["FallbackStepModel"]] = relationship(
        "FallbackStepModel",
        back_populates="chain",
        cascade="all",
        order_by="FallbackStepModel.seq_no",
    )

    def __repr__(self) -> str:
        return f"<FallbackChainModel(id={self.id}, name={self.name})>"


class FallbackStepModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing individual steps in a fallback chain
    """

    __tablename__ = "fallback_step"

    chain_id: Mapped[str] = mapped_column(
        ForeignKey("fallback_chain.id", ondelete="CASCADE")
    )
    seq_no: Mapped[int] = mapped_column()
    model_id: Mapped[str] = mapped_column(ForeignKey("llm_model.id"))
    llm_credential_id: Mapped[str | None] = mapped_column(
        ForeignKey("llm_credential.id")
    )
    max_retries: Mapped[int] = mapped_column(default=1)
    retry_delay_ms: Mapped[int] = mapped_column(default=500)
    temperature_override: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 2))
    max_tokens_override: Mapped[int | None] = mapped_column()
    stop_sequences: Mapped[List[str] | None] = mapped_column(JSON)

    # Relationships
    chain: Mapped["FallbackChainModel"] = relationship(
        "FallbackChainModel", back_populates="fallback_steps"
    )

    model: Mapped["LLMModel"] = relationship(
        "LLMModel", back_populates="fallback_steps"
    )

    credential: Mapped["LLMCredentialModel"] = relationship(
        "LLMCredentialModel", back_populates="fallback_steps"
    )

    extraction_audits: Mapped[List["ExtractionAuditModel"]] = relationship(
        "ExtractionAuditModel", back_populates="chain_step"
    )

    # Unique constraint for chain_id and seq_no combination
    __table_args__ = (UniqueConstraint("chain_id", "seq_no", name="uq_chain_seq_no"),)

    def __repr__(self) -> str:
        return f"<FallbackStepModel(id={self.id}, chain_id={self.chain_id}, seq_no={self.seq_no})>"
