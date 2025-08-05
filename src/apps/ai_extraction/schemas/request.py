from datetime import date
from decimal import Decimal
from typing import Literal, Optional, Union

from pydantic import Field, field_validator
from ulid import ULID

from core.utils import CamelCaseModel

# Document type literal
DocType = Literal["CIOMS", "IRMS", "AER", "MEDWATCH", "LFTA", "YELLOW_CARD"]

# Agent code literal
AgentCode = Literal["PATIENT", "AE", "PRODUCT", "CASE", "LABORATORY"]


class PromptTemplateCreateRequest(CamelCaseModel):
    """Request schema for creating a prompt template"""

    doc_type_id: ULID = Field(..., description="Document type ID")
    version: int = Field(..., description="Template version number")
    language: str = Field("en", description="Template language code (e.g., 'en')")
    temperature: Union[float, str] = Field(
        0.0, description="Sampling temperature (0.0 to 1.0)"
    )
    top_p: Union[float, str] = Field(
        1.0, description="Nucleus sampling parameter (0.0 to 1.0)"
    )
    max_tokens: int = Field(1024, description="Maximum tokens to generate")
    template_body: str = Field(..., description="Template content with placeholders")

    @field_validator("temperature", "top_p")
    @classmethod
    def validate_decimal_range(cls, v):
        """Validate that decimal values are within valid range (0.0 to 1.0)"""
        try:
            num = float(v)
            if not 0.0 <= num <= 1.0:
                raise ValueError("must be between 0.0 and 1.0")
            return num
        except (ValueError, TypeError) as e:
            raise ValueError("must be a valid number between 0.0 and 1.0") from e


class ExtractionRequest(CamelCaseModel):
    """Request schema for document extraction"""

    request_id: ULID = Field(
        ..., description="External correlation ULID for idempotency"
    )
    file_path: str = Field(..., description="Path to input document (PDF/TXT)")
    doc_type: DocType = Field(
        ..., description="Document type driving prompt & schema selection"
    )


class RedactionRequest(CamelCaseModel):
    """Request schema for PDF redaction"""

    src_path: str = Field(..., description="Source PDF path")
    dst_path: str = Field(..., description="Destination PDF path")
    patterns: list[str] = Field(..., description="Regex patterns for redaction")


class ValidationRequest(CamelCaseModel):
    """Request schema for JSON validation"""

    json_str: str = Field(..., description="JSON string to validate")
    doc_type: DocType = Field(..., description="Document type for schema selection")


class ExtractionAgentCreateRequest(CamelCaseModel):
    """Request schema for creating an extraction agent"""

    doc_type_id: ULID = Field(..., description="Document type ID")
    template_id: ULID = Field(..., description="Prompt template ID")
    chain_id: ULID = Field(..., description="Fallback chain ID")
    credential_id: ULID = Field(..., description="LLM credential ID")
    code: str = Field(..., description="Agent code")
    description: str = Field(..., description="Agent description")
    is_active: bool = Field(True, description="Whether the agent is active")
    seq_no: int = Field(1, description="Sequence number for ordering")


# LLM Provider Request Schemas
class LLMProviderCreateRequest(CamelCaseModel):
    """Request schema for creating an LLM provider"""

    name: str = Field(..., description="Provider name (e.g., OpenAI, Anthropic)")
    base_url: Optional[str] = Field(None, description="Base URL for the provider API")
    is_active: bool = Field(True, description="Whether the provider is active")


# LLM Model Request Schemas
class LLMModelCreateRequest(CamelCaseModel):
    """Request schema for creating an LLM model"""

    provider_id: ULID = Field(..., description="Provider ID")
    name: str = Field(..., description="Model name (e.g., gpt-4, claude-3)")
    context_tokens: int = Field(..., description="Maximum context tokens")
    input_price_1k: Union[Decimal, str] = Field(
        ..., description="Input price per 1K tokens"
    )
    output_price_1k: Union[Decimal, str] = Field(
        ..., description="Output price per 1K tokens"
    )
    launch_date: Optional[date] = Field(None, description="Model launch date")
    is_deprecated: bool = Field(False, description="Whether the model is deprecated")

    @field_validator("input_price_1k", "output_price_1k")
    @classmethod
    def validate_price(cls, v):
        """Validate that price values are non-negative"""
        try:
            num = Decimal(str(v))
            if num < 0:
                raise ValueError("must be non-negative")
            return num
        except (ValueError, TypeError) as e:
            raise ValueError("must be a valid non-negative number") from e


# LLM Credential Request Schemas
class LLMCredentialCreateRequest(CamelCaseModel):
    """Request schema for creating an LLM credential"""

    provider_id: ULID = Field(..., description="Provider ID")
    alias: Optional[str] = Field(
        None, description="Credential alias for identification"
    )
    api_key: str = Field(..., description="API key (will be encrypted)")
    rate_limit_rpm: Optional[int] = Field(
        None, description="Rate limit requests per minute"
    )
    is_active: bool = Field(True, description="Whether the credential is active")

    @field_validator("rate_limit_rpm")
    @classmethod
    def validate_rate_limit(cls, v):
        """Validate that rate limit is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError("must be positive")
        return v
