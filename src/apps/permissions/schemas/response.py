from typing import Any

from core.utils.schema import CamelCaseModel


class BasePermissionResponse(CamelCaseModel):
    """Base permission response model."""

    id: str
    name: str
    slug: str | None = None
    description: str | None = None
    permission_metadata: dict[str, Any] | None = None
    client_id: str | None = None


class ListPermissionResponse(CamelCaseModel):
    """List permission response model."""

    id: str
    name: str
    permissions: dict | None = None


class PermissionResponse(CamelCaseModel):
    """Permission response model."""

    id: str
    name: str
    description: str | None = None
    permission_metadata: dict[str, Any] | None = None


class AssignPermissionResponse(CamelCaseModel):
    """Assign permission response model."""

    id: str
    name: str
    permission_keys: dict


class AssignPermissionListResponse(CamelCaseModel):
    """Assign permission list response model."""

    id: str
    parent_module: str
    modules: list[AssignPermissionResponse]
