"""Request Schema for creating,updating,login operations of user."""

from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from apps.users.exceptions import (
    PhoneOrEmailRequiredError,
    PhoneRequiredError,
    UserMfaCodeRequiredError,
)
from core.common_helpers import validate_string_fields
from core.utils.phone_validator import validate_and_format_phone_number


class LoginRequest(BaseModel):
    """Request model for user login."""

    username: str | None = None
    phone: str | None = None
    email: str | None = None
    otp: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        return v.lower() if v else v

    @model_validator(mode="after")
    def check_login_fields(self) -> "LoginRequest":
        # If OTP is present, phone is required
        if self.otp is not None and not self.phone:
            raise PhoneRequiredError
        # If both OTP and email/phone are not present, raise error
        if self.otp is None and not (self.phone or self.email):
            raise PhoneOrEmailRequiredError
        return self


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""

    first_name: str = Field(..., min_length=1, max_length=30, description="First name of the user")
    last_name: str = Field(..., min_length=1, max_length=30, description="Last name of the user")
    phone: Optional[str] = Field(None, min_length=1, max_length=16, description="Phone number of the user")
    email: EmailStr = Field(..., description="Email of the user")

    _validate_string_fields = model_validator(mode="before")(validate_string_fields)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        return v.lower() if v else v

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, _v: str) -> str | None:
        """Validate Phone number."""
        if _v:
            return validate_and_format_phone_number(_v)
        return None


class UpdateUserRequest(BaseModel):
    """Request model for updating a user."""

    first_name: str = Field(..., min_length=1, max_length=30, description="First name of the user")
    last_name: str = Field(..., min_length=1, max_length=30, description="Last name of the user")
    phone: Optional[str] = Field(None, min_length=1, max_length=16, description="Phone number of the user")
    email: EmailStr = Field(..., description="Email of the user")
    reason: str = Field(..., description="Reason for updating the user")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        return v.lower() if v else v

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, _v: str) -> str | None:
        """Validate Phone number."""
        if _v:
            return validate_and_format_phone_number(_v)
        return None

    _validate_string_fields = model_validator(mode="before")(validate_string_fields)


class UserClientAssignment(BaseModel):
    """Model for a single client assignment with role."""

    client_id: str
    role_id: str


class AssignUserClientsRequest(BaseModel):
    """Request model for assigning clients, roles, and user types to a user."""

    assignments: list[UserClientAssignment]

