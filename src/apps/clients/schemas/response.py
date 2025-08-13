from pydantic import Field
from typing import Optional, List
from datetime import datetime
from core.utils import CamelCaseModel
from apps.media.schemas.response import MediaResponse


class ClientResponse(CamelCaseModel):
    """Schema for client information in responses."""
    
    id: str = Field(..., description="Unique identifier for the client")
    name: str = Field(..., description="Name of the client")
    code: str = Field(..., description="Unique code for the client")
    slug: str = Field(..., description="URL-friendly slug for the client")
    description: Optional[str] = Field(None, description="Description of the client")
    meta_data: Optional[dict] = Field(None, description="Additional metadata for the client")
    media: Optional[MediaResponse] = Field(None, description="Associated media file")
    is_active: bool = Field(..., description="Whether the client is active")
    created_at: datetime = Field(..., description="When the client was created")
    updated_at: datetime = Field(..., description="When the client was last updated")
    created_by: Optional[str] = Field(None, description="ID of the user who created the client")
    updated_by: Optional[str] = Field(None, description="ID of the user who last updated the client")


class ClientListResponse(CamelCaseModel):
    """Schema for paginated list of clients."""
    
    items: List[dict] = Field(..., description="List of clients with id, name, and code only")
    total: int = Field(..., description="Total number of clients")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class CreateClientResponse(CamelCaseModel):
    """Schema for client creation response."""
    
    id: str = Field(..., description="ID of the created client")
    message: str = Field(..., description="Success message")


class UpdateClientResponse(CamelCaseModel):
    """Schema for client update response."""
    
    id: str = Field(..., description="ID of the updated client")
    message: str = Field(..., description="Success message")


class DeleteClientResponse(CamelCaseModel):
    """Schema for client deletion response."""
    
    id: str = Field(..., description="ID of the deleted client")
    message: str = Field(..., description="Success message")