from typing import Any

from apps.permissions.schemas import BasePermissionResponse
from core.utils.schema import CamelCaseModel


class BaseModuleResponse(CamelCaseModel):
    """Base module response model."""

    id: str
    name: str
    slug: str
    description: str | None = None
    module_metadata: dict[str, Any] | None = None
    permissions: list[BasePermissionResponse] = []
    child_modules: list["BaseModuleResponse"] = []


class ModuleResponse(CamelCaseModel):
    """Model for representing module response."""

    id: str
    name: str
    slug: str
    description: str | None = None
    module_metadata: dict[str, Any] | None = None
    child_modules: list[BaseModuleResponse] = []
    permissions: list[BasePermissionResponse] = []
