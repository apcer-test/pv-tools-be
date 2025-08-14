from typing import Any

from pydantic import BaseModel, Field


class ModulePermissionAssignment(BaseModel):
    module_id: str
    permission_ids: list[str]


class CreateRoleRequest(BaseModel):
    """Request model for creating a role."""

    name: str
    module_permissions: list[ModulePermissionAssignment] | None = None
    description: str | None = None
    role_metadata: dict[str, Any] | None = None


class UpdateRoleRequest(CreateRoleRequest):
    """Request model for updating a role."""

    reason: str = Field(..., description="Reason for updating the role")
