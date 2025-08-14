from typing import Any

from pydantic import BaseModel


class BaseUserTypeResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    user_type_metadata: dict[str, Any] | None = None
