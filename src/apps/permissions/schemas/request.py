"""request schema for representing permission information."""

from typing import Any

from pydantic import BaseModel, Field


class CreatePermissionRequest(BaseModel):
    """Request model for creating a permission."""

    name: str
    slug: str | None = None


class UpdatePermissionRequest(BaseModel):
    """Request model for updating a permission."""

    name: str
    slug: str | None = None
    description: str | None = None
    permission_metadata: dict[str, Any] | None = None
