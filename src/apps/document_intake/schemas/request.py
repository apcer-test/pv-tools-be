from pydantic import BaseModel, Field
from typing import Optional
from apps.ai_extraction.schemas.request import DocType


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload and extraction"""
    doc_type: DocType = Field(..., description="Document type for extraction (CIOMS, IRMS, AER, LAB_REPORT, UNKNOWN)") 