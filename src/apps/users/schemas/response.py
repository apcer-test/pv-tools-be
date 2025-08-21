"""Response Model for user."""

from datetime import datetime
from typing import Any, Optional

from apps.roles.schemas.response import ModuleBasicResponse
from apps.users.constants import UserAuthAction
from core.types import LoginActivityStatus
from core.utils.schema import CamelCaseModel


class RoleResponse(CamelCaseModel):
    """Response model for role information."""

    id: str | None
    name: str | None


class LoginResponse(CamelCaseModel):
    """Response model for user login."""

    access_token: str | None
    refresh_token: str | None
    mfa_token: str | None
    user_id: str
    session_id: str | None
    roles: list[str] | None = []
    scopes: dict[str, list[str]]
    action: UserAuthAction | None
    message: str | None = None


class UserLoginResponse(CamelCaseModel):
    """Response model for user login."""

    message: str
    access_token: str


class RefreshTokenResponse(CamelCaseModel):
    """Response model for refreshing an access token."""

    access_token: str


class CreateUserResponse(CamelCaseModel):
    """Response model containing information about a created user."""

    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True


class UpdateUserResponse(CamelCaseModel):
    """Response model for updated user's information."""

    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    is_active: bool
    updated_at: datetime
    message: str

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True


class UserClientAssignmentResponse(CamelCaseModel):
    """Response model for a single client assignment."""

    client_id: str
    role_id: str
    status: str  # "assigned" or "updated"


class AssignUserClientsResponse(CamelCaseModel):
    """Response model for user client assignment operation."""

    user_id: str
    assignments: list[UserClientAssignmentResponse]
    message: str


class PermissionResponse(CamelCaseModel):
    """Response model for permission information."""

    id: str
    name: str
    key: str


class UserResponse(CamelCaseModel):
    """Response model for getting information of self."""

    id: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    roles: list[RoleResponse] | None
    description: str | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None
    is_active: bool
    created_by: str | None = None
    updated_by: str | None = None


class ClientResponse(CamelCaseModel):
    """Response model for client information."""

    id: str
    name: str


class UserAssignResponse(CamelCaseModel):
    """Response model for user assign information."""

    role_name: str
    client_name: str


class UserAssignmentsResponse(CamelCaseModel):
    """Response model for user assignments information."""

    role: RoleResponse | None
    client: ClientResponse | None


class ListUserResponse(CamelCaseModel):
    """Response model for getting user's information."""

    id: str
    email: str | None = None
    phone: str | None = None
    is_active: bool
    first_name: str
    last_name: str
    assigns: list[UserAssignmentsResponse]
    description: str | None = None
    meta_data: dict[str, Any] | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime | None


class UserStatusResponse(CamelCaseModel):
    """Response model for user status information."""

    id: str
    is_active: bool
    message: str


class UserSelfRoleResponse(CamelCaseModel):
    """Response model for user self role information."""

    id: str
    name: str
    slug: str
    modules: list[ModuleBasicResponse] | None = None


class UserSelfResponse(CamelCaseModel):
    """Response model for user self information."""

    id: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    role: UserSelfRoleResponse | None = None
    is_active: bool


class UserMiniOut(CamelCaseModel):
    """Response model for user mini information."""

    id: str
    email: str


class ClientMiniOut(CamelCaseModel):
    """Response model for client mini information."""

    id: str
    name: str


class LoginActivityOut(CamelCaseModel):
    """Response model for login activity information."""

    id: str
    user: Optional[UserMiniOut] = None
    client: Optional[ClientMiniOut] = None
    status: LoginActivityStatus
    activity: str
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
