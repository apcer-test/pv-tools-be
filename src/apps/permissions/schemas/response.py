from typing import Any

from pydantic import BaseModel


class BasePermissionResponse(BaseModel):
    id: str
    name: str
    slug: str | None = None
    description: str | None = None
    permission_metadata: dict[str, Any] | None = None
    client_id: str | None = None

class ListPermissionResponse(BaseModel):
    id: str
    name: str
    permissions: dict | None = None


class PermissionResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    permission_metadata: dict[str, Any] | None = None


class AssignPermissionResponse(BaseModel):
    id: str
    name: str
    permission_keys: dict


class AssignPermissionListResponse(BaseModel):
    id: str
    parent_module: str
    modules: list[AssignPermissionResponse]
