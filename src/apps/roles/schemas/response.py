"""Response Model for rolemodel."""

from typing import Any

from pydantic import BaseModel

from apps.modules.schemas import ModuleResponse


class BaseRoleResponse(BaseModel):
    """role response for role operations."""

    id: int
    name: str
    slug: str
    description: str | None = None
    role_metadata: dict[str, Any] | None = None


class RoleResponse(BaseRoleResponse):
    """role response for role operations."""

    modules: list[ModuleResponse]
