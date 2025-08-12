"""Response Model for user."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr

from apps.roles.schemas import RoleResponse as AliasedRoleResponse
from apps.users.constants import UserAuthAction


class RoleResponse(BaseModel):
    """Response model for role information."""

    id: int | None
    name: str | None


class LoginResponse(BaseModel):
    """Response model for user login."""

    access_token: str | None
    refresh_token: str | None
    mfa_token: str | None
    user_id: int
    username: str | None
    session_id: str | None
    roles: list[str] | None = []
    scopes: dict[str, list[str]]
    action: UserAuthAction | None
    message: str | None = None


class UserLoginResponse(BaseModel):
    """Response model for user login."""

    message: str
    access_token: str


class RefreshTokenResponse(BaseModel):
    """Response model for refreshing an access token."""

    access_token: str


class CreateUserResponse(BaseModel):
    """Response model containing information about a created user."""

    id: int
    name: str
    username: str | None

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True


class BaseUserResponse(BaseModel):
    """Response model for user information."""

    id: int
    username: str | None
    email: str | None = None
    phone: str | None = None
    role_ids: list[int] | None = None
    type_id: int | None = None
    subtype_id: int | None = None
    description: str | None = None
    user_metadata: dict[str, Any] | None = None
    app_id: int
    tenant_id: int


class UserStatusResponse(BaseModel):
    """Response model for user with status information."""

    id: int
    username: str | None
    email: str | None = None
    phone: str | None = None
    app_id: int
    is_active: bool


class UpdateUserResponse(BaseModel):
    """Response model for updated user's information."""

    id: int
    username: str | None
    email: EmailStr | None = None
    phone: str | None = None
    roles: list[RoleResponse]
    user_type_id: int | None = None
    user_subtype_id: int | None = None
    description: str | None = None
    user_metadata: dict[str, Any] | None = None
    app_id: int | None


class PermissionResponse(BaseModel):
    """Response model for permission information."""

    id: int
    name: str
    key: str


class UserTypeResponse(BaseModel):
    """Response model for type information."""

    id: int | None
    name: str | None


class UserSubTypeResponse(BaseModel):
    """Response model for subtype information."""

    id: int | None
    name: str | None


class TenantAppResponse(BaseModel):
    """Response model for tenant_app information."""

    id: int | None
    app_name: str
    tenant_id: int | None


class UserResponse(BaseModel):
    """response model for getting information of self."""

    id: int
    username: str | None
    email: str | None = None
    phone: str | None = None
    roles: list[AliasedRoleResponse] | None
    type: UserTypeResponse | None
    subtype: UserSubTypeResponse | None
    description: str | None = None
    user_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None
    mfa_enabled: bool | None
    mfa_enrolled: bool | None


class ListUserResponse(UserStatusResponse):
    """Response model for getting user's information."""

    roles: list[RoleResponse]
    type: UserTypeResponse
    subtype: UserSubTypeResponse
    description: str | None = None
    user_metadata: dict[str, Any] | None = None


class GenerateOTPResponse(BaseModel):
    """Response model for generating OTP."""

    otp: str


class MFASetupResponse(BaseModel):
    """Response model for MFA setup."""

    qrcode_base64: str
    backup_codes: list[str]
    mfa_token: str


class MFAVerifiedResponse(BaseModel):
    """Response model for MFA verified."""

    access_token: str
    refresh_token: str
    user_id: int
    username: str | None
    session_id: str | None
    roles: list[str] | None = []
    scopes: dict[str, list[str]]


class MFAResetResponse(BaseModel):
    """Response model for MFA reset."""

    mfa_token: str


class MFAEnableResponse(BaseModel):
    """Response model for MFA enable."""

    message: str
    mfa_token: str | None
    action: UserAuthAction | None


class AdditionalClaimsResponse(BaseModel):
    """Response model for additional claims."""

    roles: list[str] | None = None
    email: str | None = None
    is_mfa_enabled: str | None = None
