from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ulid import ULID

from core.utils import CamelCaseModel


class DocumentExtractionResponse(CamelCaseModel):
    """Response schema for document extraction results"""
    request_id: ULID = Field(..., description="Correlation UUID for the extraction request")
    status: str = Field(..., description="Status of extraction (success/error)")
    data: Optional[Dict[str, Any]] = Field(None, description="Extracted data from document")
    error_code: Optional[str] = Field(None, description="Error code if extraction failed")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")
    failed_at_step: Optional[str] = Field(None, description="Step where extraction failed") 
