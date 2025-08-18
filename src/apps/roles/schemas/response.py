"""Response Model for rolemodel."""

from typing import Any, List

from pydantic import BaseModel


class UserBasicInfo(BaseModel):
    """Basic user information for role responses."""
    
    id: str
    name: str


class PermissionBasicInfo(BaseModel):
    """Basic permission information for role responses."""
    
    id: str
    name: str


class ModuleBasicResponse(BaseModel):
    """Basic module response with permission IDs only."""
    
    id: str
    name: str
    slug: str
    description: str | None = None
    module_metadata: dict[str, Any] | None = None
    child_modules: list["ModuleBasicResponse"] = []
    permissions: List[PermissionBasicInfo] = []


class BaseRoleResponse(BaseModel):
    """role response for role operations."""

    id: str
    name: str
    slug: str
    description: str | None = None
    role_metadata: dict[str, Any] | None = None
    users: List[UserBasicInfo] = []
    is_active: bool


class RoleResponse(BaseRoleResponse):
    """role response for role operations."""

    modules: list[ModuleBasicResponse]


class RoleStatusResponse(BaseModel):
    """Role status response."""

    id: str
    is_active: bool
    message: str

