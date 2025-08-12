"""request schema for representing permission information."""

from typing import Any

from pydantic import BaseModel


class CreatePermissionRequest(BaseModel):
    """Request model for creating,updating a permission."""

    name: str
    slug: str | None = None
    description: str | None = None
    permission_metadata: dict[str, Any] | None = None
