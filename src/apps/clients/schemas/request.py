from pydantic import Field, validator
from typing import Optional
from apps.media.schemas.request import MediaRequest
from core.utils import CamelCaseModel


class CreateClientRequest(CamelCaseModel):
    """Schema for creating a new client."""
    
    name: str = Field(..., min_length=1, max_length=128, description="Name of the client")
    code: str = Field(..., min_length=1, max_length=16, description="Unique code for the client")
    slug: str = Field(..., min_length=1, max_length=128, description="URL-friendly slug for the client")
    description: Optional[str] = Field(None, max_length=255, description="Description of the client")
    meta_data: Optional[dict] = Field(None, description="Additional metadata for the client")
    media: Optional[MediaRequest] = Field(None, description="Media file information")
    is_active: bool = Field(True, description="Whether the client is active")

    @validator('code')
    def validate_code(cls, v):
        """Validate that code contains only alphanumeric characters and hyphens."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must contain only alphanumeric characters, hyphens, and underscores')
        return v.upper()

    @validator('slug')
    def validate_slug(cls, v):
        """Validate that slug contains only lowercase letters, numbers, and hyphens."""
        if not v.replace('-', '').replace('_', '').islower() and not v.replace('-', '').replace('_', '').isdigit():
            raise ValueError('Slug must contain only lowercase letters, numbers, hyphens, and underscores')
        return v


class UpdateClientRequest(CamelCaseModel):
    """Schema for updating an existing client."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="Name of the client")
    code: Optional[str] = Field(None, min_length=1, max_length=16, description="Unique code for the client")
    slug: Optional[str] = Field(None, min_length=1, max_length=128, description="URL-friendly slug for the client")
    description: Optional[str] = Field(None, max_length=255, description="Description of the client")
    meta_data: Optional[dict] = Field(None, description="Additional metadata for the client")
    media: Optional[MediaRequest] = Field(None, description="Media file information")
    is_active: Optional[bool] = Field(None, description="Whether the client is active")

    @validator('code')
    def validate_code(cls, v):
        """Validate that code contains only alphanumeric characters and hyphens."""
        if v is not None:
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Code must contain only alphanumeric characters, hyphens, and underscores')
            return v.upper()
        return v

    @validator('slug')
    def validate_slug(cls, v):
        """Validate that slug contains only lowercase letters, numbers, and hyphens."""
        if v is not None:
            if not v.replace('-', '').replace('_', '').islower() and not v.replace('-', '').replace('_', '').isdigit():
                raise ValueError('Slug must contain only lowercase letters, numbers, hyphens, and underscores')
        return v


class ListClientsRequest(CamelCaseModel):
    """Schema for listing clients with filters and pagination."""
    
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term across name, code, and description")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    sort_by: Optional[str] = Field(None, description="Sort field (name, code, created_at, updated_at)")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")