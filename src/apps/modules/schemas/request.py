"""Request schema for representing modules."""

from typing import Any

from pydantic import BaseModel, Field


class CreateModuleRequest(BaseModel):
    """Request model for creating, updating a permission."""

    name: str
    slug: str | None = None
    parent_module_id: int | None = None
    permissions: list[int] | None = None


class UpdateModuleRequest(BaseModel):
    """Request model for creating, updating a module."""

    name: str
    permissions: list[int] | None = None
    parent_module_id: int | None = None
    slug: str | None = None
    description: str | None = None
    module_metadata: dict[str, Any] | None = None
    reason: str = Field(..., description="Reason for updating the module")
