from typing import Any

from pydantic import BaseModel, Field


class ModulePermissionAssignment(BaseModel):
    module_id: int
    permission_ids: list[int]


class CreateRoleRequest(BaseModel):
    """Request model for creating a role."""

    name: str
    module_permissions: list[ModulePermissionAssignment] | None = None
    slug: str | None = None


class UpdateRoleRequest(BaseModel):
    """Request model for updating a role."""

    name: str | None = None
    module_permissions: list[ModulePermissionAssignment] | None = None
    slug: str | None = None
    description: str | None = None
    role_metadata: dict[str, Any] | None = None
    reason: str = Field(..., description="Reason for updating the role")
