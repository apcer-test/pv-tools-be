from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, DECIMAL, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from decimal import Decimal
from datetime import date

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin
from apps.ai_extraction.models.doctype import DocTypeModel
from apps.ai_extraction.models.fallback import FallbackChainModel

if TYPE_CHECKING:
    from apps.ai_extraction.models.fallback import FallbackChainModel, FallbackStepModel
    from apps.ai_extraction.models.extraction_audit import ExtractionAuditModel


class LLMProviderModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing LLM providers (OpenAI, Anthropic, etc.)
    """
    __tablename__ = "llm_provider"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    base_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships - Using 'all' cascade without delete-orphan for soft delete support
    models: Mapped[List["LLMModel"]] = relationship(
        "LLMModel", 
        back_populates="provider",
        cascade="all"
    )
    
    credentials: Mapped[List["LLMCredentialModel"]] = relationship(
        "LLMCredentialModel",
        back_populates="provider", 
        cascade="all"
    )

    def __repr__(self) -> str:
        return f"<LLMProviderModel(id={self.id}, name={self.name})>"


class LLMModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing specific LLM models from providers
    """
    __tablename__ = "llm_model"

    provider_id: Mapped[str] = mapped_column(ForeignKey("llm_provider.id"))
    name: Mapped[str] = mapped_column(String(255))
    context_tokens: Mapped[int] = mapped_column()
    input_price_1k: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))
    output_price_1k: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))
    launch_date: Mapped[date | None] = mapped_column(Date)
    is_deprecated: Mapped[bool] = mapped_column(default=False)

    # Relationships
    provider: Mapped["LLMProviderModel"] = relationship(
        "LLMProviderModel", 
        back_populates="models"
    )
    
    fallback_steps: Mapped[List["FallbackStepModel"]] = relationship(
        "FallbackStepModel",
        back_populates="model"
    )
    
    extraction_audits: Mapped[List["ExtractionAuditModel"]] = relationship(
        "ExtractionAuditModel",
        back_populates="model"
    )

    # Unique constraint for provider_id and name combination
    __table_args__ = (
        UniqueConstraint('provider_id', 'name', name='uq_provider_model_name'),
    )

    def __repr__(self) -> str:
        return f"<LLMModel(id={self.id}, name={self.name}, provider_id={self.provider_id})>"


class LLMCredentialModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing LLM credentials for different providers
    """
    __tablename__ = "llm_credential"

    provider_id: Mapped[str] = mapped_column(ForeignKey("llm_provider.id"))
    alias: Mapped[str | None] = mapped_column(String(255))
    api_key_enc: Mapped[str | None] = mapped_column(Text)
    rate_limit_rpm: Mapped[int | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    provider: Mapped["LLMProviderModel"] = relationship(
        "LLMProviderModel", 
        back_populates="credentials"
    )
    
    fallback_steps: Mapped[List["FallbackStepModel"]] = relationship(
        "FallbackStepModel",
        back_populates="credential"
    )
    
    # Unique constraint for provider_id and alias combination
    __table_args__ = (
        UniqueConstraint('provider_id', 'alias', name='uq_provider_credential_alias'),
    )

    def __repr__(self) -> str:
        return f"<LLMCredentialModel(id={self.id}, alias={self.alias}, provider_id={self.provider_id})>" 


class ExtractionAgentModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model representing extraction agents
    """
    __tablename__ = "extraction_agent"

    doc_type_id: Mapped[str] = mapped_column(ForeignKey("doc_type.id"))
    code: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    prompt_template_id: Mapped[str] = mapped_column(ForeignKey("prompt_template.id"))
    fallback_chain_id: Mapped[str] = mapped_column(ForeignKey("fallback_chain.id"))
    llm_credential_id: Mapped[str] = mapped_column(ForeignKey("llm_credential.id")) # remove
    is_active: Mapped[bool] = mapped_column(default=True)
    sequence_no: Mapped[int] = mapped_column(unique=True)
    preferred_model: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    doc_type: Mapped["DocTypeModel"] = relationship(
        "DocTypeModel", 
        back_populates="extraction_agents"
    )

    fallback_chain: Mapped["FallbackChainModel"] = relationship(
        "FallbackChainModel"
    )
    
    credential: Mapped["LLMCredentialModel"] = relationship(
        "LLMCredentialModel"
    )


    __table_args__ = (
        UniqueConstraint('doc_type_id', 'sequence_no', name='uq_doc_type_sequence_no'),
    )


    def __repr__(self) -> str:
        return f"<ExtractionAgentModel(id={self.id}, code={self.code}, doc_type_id={self.doc_type_id})>"
