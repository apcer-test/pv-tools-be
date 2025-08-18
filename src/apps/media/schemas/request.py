from pydantic import BaseModel, Field, validator
from typing import Optional
from core.utils import CamelCaseModel


class MediaRequest(CamelCaseModel):
    """Schema for media file information when creating/updating a client."""
    
    file_name: str = Field(..., min_length=1, max_length=128, description="Name of the media file")
    file_path: str = Field(..., min_length=1, max_length=255, description="Path/URL of the media file")
