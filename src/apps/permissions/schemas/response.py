from typing import Any

from pydantic import BaseModel


class BasePermissionResponse(BaseModel):
    id: int
    name: str
    slug: str | None = None
    description: str | None = None
    permission_metadata: dict[str, Any] | None = None


class ListPermissionResponse(BaseModel):
    id: int
    name: str
    permissions: dict | None = None


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    permission_metadata: dict[str, Any] | None = None


class AssignPermissionResponse(BaseModel):
    id: int
    name: str
    permission_keys: dict


class AssignPermissionListResponse(BaseModel):
    id: int
    parent_module: str
    modules: list[AssignPermissionResponse]
