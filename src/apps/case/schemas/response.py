from datetime import datetime
from typing import List, Optional

from pydantic import Field

from apps.case.types.component_types import ComponentType
from core.utils import CamelCaseModel


class CaseNumberComponentResponse(CamelCaseModel):
    """Response schema for case number component"""

    id: str = Field(..., description="Component ID")
    component_type: ComponentType = Field(..., description="Type of the component")
    size: Optional[int] = Field(None, description="Size of the component")
    prompt: Optional[str] = Field(None, description="Prompt text for PROMPT type")
    ordering: int = Field(..., description="Component order")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class CaseNumberConfigurationResponse(CamelCaseModel):
    """Response schema for case number configuration"""

    id: str = Field(..., description="Configuration ID")
    name: str = Field(..., description="Configuration name")
    separator: str = Field(..., description="Component separator")
    is_active: bool = Field(..., description="Active status")
    components: List[CaseNumberComponentResponse] = Field(
        ..., description="Configuration components"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CaseResponse(CamelCaseModel):
    """Response schema for case"""

    id: str = Field(..., description="Case ID")
    case_number: str = Field(..., description="Generated case number")
    config_id: str = Field(..., description="Configuration ID used")
    version: str = Field(..., description="Case version")
    meta_data: Optional[dict] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
