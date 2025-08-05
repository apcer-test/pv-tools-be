from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from ulid import ULID

from core.utils import CamelCaseModel


class ExtractionDataResult(CamelCaseModel):
    """Success response for document extraction"""

    request_id: ULID
    doc_type: str | None
    extracted_at: datetime | None
    data: dict | None
    model_used: str | None
    tokens_prompt: int | None
    tokens_completion: int | None
    cost_usd: Decimal | None
    latency_ms: int | None
    template_id: ULID | None
    agent_code: str | None


class ExtractionResult(CamelCaseModel):
    """Response for document extraction"""

    request_id: ULID
    doc_type: str | None
    data: dict | None


class ExtractionError(CamelCaseModel):
    """Error response for document extraction"""

    request_id: ULID
    error_code: str
    error_message: str
    failed_at_step: str | None
    retry_count: int | None
    created_at: datetime


class PreProcessResult(CamelCaseModel):
    """Response for preprocessing operations"""

    text_content: str
    file_type: str
    page_count: int | None
    word_count: int


class ValidationResult(CamelCaseModel):
    """Response for schema validation"""

    is_valid: bool
    validated_data: dict | None
    errors: list[str] | None
    repaired: bool


class PromptTemplateResponse(CamelCaseModel):
    """Response model for prompt template"""

    id: ULID
    doc_type_id: ULID
    version: int
    language: str
    temperature: float
    top_p: float
    max_tokens: int
    template_body: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class ExtractionAgentResponse(CamelCaseModel):
    """Response model for extraction agent"""

    id: ULID
    code: str
    name: str
    description: str | None
    sequence_no: int
    is_active: bool


class DocumentTypeResponse(CamelCaseModel):
    """Response model for document type with related data"""

    id: ULID
    code: str
    description: str | None
    prompt_templates: list[PromptTemplateResponse]
    extraction_agents: list[ExtractionAgentResponse]


class LLMCallResult(CamelCaseModel):
    """Response for LLM gateway calls"""

    response_text: str
    model_used: str
    tokens_prompt: int
    tokens_completion: int
    cost_usd: Decimal
    latency_ms: int
    provider: str


# LLM Provider Response Schemas
class LLMProviderResponse(CamelCaseModel):
    """Response model for LLM provider"""

    id: ULID
    name: str
    base_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class LLMProviderDetailResponse(CamelCaseModel):
    """Response model for LLM provider with related data"""

    id: ULID
    name: str
    base_url: Optional[str] = None
    is_active: bool
    models: List["LLMModelResponse"] = []
    credentials: List["LLMCredentialResponse"] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


# LLM Model Response Schemas
class LLMModelResponse(CamelCaseModel):
    """Response model for LLM model"""

    id: ULID
    provider_id: ULID
    name: str
    context_tokens: int
    input_price_1k: Decimal
    output_price_1k: Decimal
    launch_date: Optional[date] = None
    is_deprecated: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class LLMModelDetailResponse(CamelCaseModel):
    """Response model for LLM model with provider details"""

    id: ULID
    provider_id: ULID
    provider_name: str
    name: str
    context_tokens: int
    input_price_1k: Decimal
    output_price_1k: Decimal
    launch_date: Optional[date] = None
    is_deprecated: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# LLM Credential Response Schemas
class LLMCredentialResponse(CamelCaseModel):
    """Response model for LLM credential (without API key)"""

    id: ULID
    provider_id: ULID
    alias: Optional[str] = None
    rate_limit_rpm: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class LLMCredentialDetailResponse(CamelCaseModel):
    """Response model for LLM credential with provider details"""

    id: ULID
    provider_id: ULID
    provider_name: str
    alias: Optional[str] = None
    rate_limit_rpm: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
