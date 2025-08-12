from typing import Any

from pydantic import BaseModel

from apps.permissions.schemas import BasePermissionResponse


class BaseModuleResponse(BaseModel):
    """Base module response model."""

    id: int
    name: str
    slug: str
    description: str | None = None
    module_metadata: dict[str, Any] | None = None
    permissions: list[BasePermissionResponse] = []
    child_modules: list["BaseModuleResponse"] = []


class ModuleResponse(BaseModel):
    """Model for representing module response."""

    id: int
    name: str
    slug: str
    description: str | None = None
    module_metadata: dict[str, Any] | None = None
    child_modules: list[BaseModuleResponse] = []
    permissions: list[BasePermissionResponse] = []
