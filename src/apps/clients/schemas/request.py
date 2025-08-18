from pydantic import Field, model_validator, validator
from typing import Optional
from apps.media.schemas.request import MediaRequest
from core.common_helpers import validate_string_fields
from core.utils import CamelCaseModel


class CreateClientRequest(CamelCaseModel):
    """Schema for creating a new client."""
    
    name: str = Field(..., min_length=1, max_length=128, description="Name of the client")
    code: str = Field(..., min_length=1, max_length=16, description="Unique code for the client")
    media: MediaRequest = Field(..., description="Media file information")
    is_active: bool = Field(True, description="Whether the client is active")

    _validate_string_fields = model_validator(mode="before")(validate_string_fields)
 
    @validator('code')
    def validate_code(cls, v):
        """Validate that code contains only alphanumeric characters and hyphens."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must contain only alphanumeric characters, hyphens, and underscores')
        return v.upper()

    @validator('name')
    def validate_name(cls, v):
        """Validate that name is not empty."""
        if v is not None and not v.strip():
            raise ValueError('Name is required')
        return v

class UpdateClientRequest(CamelCaseModel):
    """Schema for updating an existing client."""
    
    name: str = Field(..., min_length=1, max_length=128, description="Name of the client")
    code: str = Field(..., min_length=1, max_length=16, description="Unique code for the client")
    description: Optional[str] = Field(None, max_length=255, description="Description of the client")
    meta_data: Optional[dict] = Field(None, description="Additional metadata for the client")
    media: MediaRequest = Field(..., description="Media file information")
    is_active: Optional[bool] = Field(None, description="Whether the client is active")
    reason: str = Field(..., description="Reason for updating the client")

    _validate_string_fields = model_validator(mode="before")(validate_string_fields)

    @validator('code')
    def validate_code(cls, v):
        """Validate that code contains only alphanumeric characters and hyphens."""
        if v is not None:
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Code must contain only alphanumeric characters, hyphens, and underscores')
            return v.upper()
        return v

    @validator('name')
    def validate_name(cls, v):
        """Validate that name is not empty."""
        if v is not None and not v.strip():
            raise ValueError('Name is required')
        return v


class ListClientsRequest(CamelCaseModel):
    """Schema for listing clients with filters and pagination."""
    
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
    search: Optional[str] = Field(None, description="Search term for name, code, or description")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc or desc)")