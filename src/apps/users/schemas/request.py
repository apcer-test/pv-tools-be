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


class BaseUserRequest(BaseModel):
    """Request model for creating,updating a user."""

    username: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    role_ids: list[str] | None = None
    user_type_id: str | None = None
    description: str | None = None
    user_metadata: dict[str, Any] | None = None
    reason: str | None = None  # Required for update operations

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


class CreateUserRequest(BaseUserRequest):
    """Schema for creating user."""

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        return v.lower() if v else v

    @model_validator(mode="after")
    def check_email_or_phone(self) -> "CreateUserRequest":
        """Ensure at least one of email or phone is provided."""
        if not self.email and not self.phone:
            raise PhoneOrEmailRequiredError
        return self


class GenerateOTPRequest(BaseModel):
    """Schema for generating OTP."""

    phone: str


class VerifyMFARequest(BaseModel):
    """Schema for verifying MFA."""

    code: str | None = None
    remember: bool | None = None
    backup_code: str | None = None

    @model_validator(mode="after")
    def check_otp(self) -> "VerifyMFARequest":
        if self.code is None and self.backup_code is None:
            raise UserMfaCodeRequiredError
        return self


class ResetMFARequest(BaseModel):
    """Schema for resetting MFA."""

    backup_code: str


class EnableMFARequest(BaseModel):
    """Schema for enabling MFA."""

    code: str | None = None


class DisableMFARequest(BaseModel):
    """Schema for disabling MFA."""

    code: str
