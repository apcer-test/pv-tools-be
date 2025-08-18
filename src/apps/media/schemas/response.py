from pydantic import Field
from datetime import datetime
from core.utils import CamelCaseModel


class MediaResponse(CamelCaseModel):
    """Schema for media file information in responses."""
    
    id: str = Field(..., description="Unique identifier for the media")
    file_name: str = Field(..., description="Name of the media file")
    file_path: str = Field(..., description="Path/URL of the media file")
    file_type: str = Field(..., description="Type of media")
    created_at: datetime = Field(..., description="When the media was created")
    updated_at: datetime = Field(..., description="When the media was last updated")