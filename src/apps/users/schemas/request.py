"""Request Schema for creating,updating,login operations of user."""

from typing import Any

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from apps.users.exceptions import (
    PhoneOrEmailRequiredError,
    PhoneRequiredError,
    UserMfaCodeRequiredError,
)
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

    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    reporting_manager_id: str | None = None

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

    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    reporting_manager_id: str | None = None
    reason: str  # Required for update operations

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


class UserClientAssignment(BaseModel):
    """Model for a single client assignment with role and user type."""

    client_id: str
    role_id: str
    user_type_id: str


class AssignUserClientsRequest(BaseModel):
    """Request model for assigning clients, roles, and user types to a user."""

    user_id: str
    assignments: list[UserClientAssignment]

