"""Request schema for user type."""

import re
from typing import Any, Self

from pydantic import BaseModel, model_validator

from apps.constants import USER_TYPE_REGEX
from apps.user_types.execeptions import InvalidTypeError


class CreateUserTypeRequest(BaseModel):
    """Request model for creating, updating a user's type."""

    name: str
    slug: str | None = None
    description: str | None = None
    user_type_metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_field(self) -> Self:
        """Validation for name."""
        self.name = self.name.strip()
        if not re.match(USER_TYPE_REGEX, self.name):
            raise InvalidTypeError

        return self
