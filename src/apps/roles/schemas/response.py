"""Response Model for rolemodel."""

from typing import Any

from core.utils.schema import CamelCaseModel


class UserBasicInfo(CamelCaseModel):
    """Basic user information for role responses."""

    id: str
    name: str


class PermissionBasicInfo(CamelCaseModel):
    """Basic permission information for role responses."""

    id: str
    name: str


class ModuleBasicResponse(CamelCaseModel):
    """Basic module response with permission IDs only."""

    id: str
    name: str
    slug: str
    description: str | None = None
    module_metadata: dict[str, Any] | None = None
    child_modules: list["ModuleBasicResponse"] = []
    permissions: list[PermissionBasicInfo] = []


class BaseRoleResponse(CamelCaseModel):
    """role response for role operations."""

    id: str
    name: str
    slug: str
    description: str | None = None
    role_metadata: dict[str, Any] | None = None
    users: list[UserBasicInfo] = []
    is_active: bool


class RoleResponse(CamelCaseModel):
    """role response for role operations."""

    modules: list[ModuleBasicResponse]


class RoleStatusResponse(CamelCaseModel):
    """Role status response."""

    id: str
    is_active: bool
    message: str
