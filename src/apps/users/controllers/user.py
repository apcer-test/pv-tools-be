"""Controller for user."""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Request, Response, status
from fastapi.params import Query
from fastapi_pagination import Page, Params

from apps.tenant_app_configs.models import TenantAppConfig
from apps.users.constants import UserSortBy
from apps.users.models.user import Users
from apps.users.schemas.request import (
    BaseUserRequest,
    ChangePasswordRequest,
    CreateUserRequest,
    DisableMFARequest,
    EnableMFARequest,
    GenerateOTPRequest,
    LoginRequest,
    ResetMFARequest,
    ResetPasswordRequest,
    VerifyMFARequest,
)
from apps.users.schemas.response import (
    BaseUserResponse,
    GenerateOTPResponse,
    ListUserResponse,
    LoginResponse,
    MFAEnableResponse,
    MFAResetResponse,
    MFASetupResponse,
    MFAVerifiedResponse,
    UpdateUserResponse,
    UserResponse,
    UserStatusResponse,
)
from apps.users.services.user import UserService
from apps.users.utils import (
    current_user,
    get_session_id_from_token,
    get_tenant_app_config,
    verify_change_password_token,
)
from core.dependencies import refresh_jwt, verify_refresh_token
from core.dependencies.auth import (
    verify_access_token,
    verify_api_keys,
    verify_mfa_setup_token,
    verify_mfa_verification_token,
)
from core.utils.schema import BaseResponse, SuccessResponse
from core.utils.set_cookies import delete_cookies

router = APIRouter(
    prefix="/{tenant_key}/{app_key}/users",
    tags=["User"],
    dependencies=[Depends(verify_api_keys)],
)


@router.post(
    "/login", status_code=status.HTTP_200_OK, name="Login user", operation_id="login"
)
async def login(
    body: Annotated[LoginRequest, Body()],
    request: Request,
    service: Annotated[UserService, Depends()],
    app_config: Annotated[TenantAppConfig, Depends(get_tenant_app_config)],
) -> BaseResponse[LoginResponse]:
    """Handles user login for a specific tenant and application.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - username (str | None): The username of the user.
      - phone (str | None): The phone number of the user.
      - email (str | None): The email address of the user.
      - password (str | None): The password of the user.
      - otp (str | None): The one-time password (OTP) provided by the user.

    Returns:
      - BaseResponse[LoginResponse]: A BaseResponse containing the login response.

    Raises:
     - UserNotFoundError: If no user with the provided username is found.
     - GeneratePasswordError: If the password cannot be generated.
     - LockAccountError: If the user's account is locked due to expiring password.
     - InvalidCredentialsError: If the provided password is incorrect.

    """
    return BaseResponse(
        data=await service.login(
            **body.model_dump(), request=request, app_config=app_config
        )
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    name="Logout User",
    operation_id="logout_user",
)
async def logout_user(
    user: Annotated[Users, Depends(current_user)],
    session_id: Annotated[str | None, Depends(get_session_id_from_token)],
    service: Annotated[UserService, Depends()],
) -> dict:
    """
    Logs out the currently authenticated user by invalidating their session and
    clearing authentication-related cookies.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.

    Returns:
      - dict: A dictionary containing a message indicating successful logout.
    """
    if user.id and session_id:
        await service.logout_user(user_id=user.id, session_id=session_id)

    response = Response(
        content=json.dumps({"message": "Logout successful"}),
        media_type="application/json",
    )
    delete_cookies(response)
    return response


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    name="Refresh Token",
    operation_id="refresh-token",
)
async def refresh_token(
    request: Request,
    service: Annotated[UserService, Depends()],
    refresh_token: Annotated[str, Depends(refresh_jwt)],
    claims: Annotated[dict[str, str], Depends(verify_refresh_token)],
    app_config: Annotated[TenantAppConfig, Depends(get_tenant_app_config)],
) -> BaseResponse[LoginResponse]:
    """
    Generates a new access token using a valid refresh token.

     Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.

    Returns:
      - BaseResponse[LoginResponse]: A response containing the new access token
        and related login metadata.

    Raises:
      - UnauthorizedError: If the refresh token is invalid or expired.

    """

    return BaseResponse(
        data=await service.refresh_token(claims, refresh_token, request, app_config)
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create User",
    operation_id="create-user",
)
async def create_user(
    body: Annotated[CreateUserRequest, Body()],
    service: Annotated[UserService, Depends()],
    tenant_app_config: Annotated[TenantAppConfig, Depends(get_tenant_app_config)],
) -> BaseResponse[BaseUserResponse]:
    """
    Creates a new user with the provided information.

    Args:
        - tenant_key (int/str): The tenant_key means tenant_id or name.
        This is required.
        - app_key (int/str): The app_key means app_id or name. This is required.
        - username (str | None): The username of the user.
        - phone (str): The phone number of the user.
        - email (str): The email address of the user.
        - role_ids (list[int] | None) : List of role IDs to assign to the user.
        - type_id (int | None) : The Type ID of the user.
        - subtype_id (int | None) : The Subtype ID of the user.
        - password (str): The password of the user.

    Returns:
        - BaseResponse[BaseUserResponse]: A response containing
        the created user's basic information.

    Raises:
        - WeakPasswordError: If the provided password is weak.
        - PhoneAlreadyExistsError: If the provided phone number already exists.
        - EmailAlreadyExistsError: If the provided email address already exists.
        - RoleNotFoundError: If any of the provided role IDs do not exist.
        - UserTypeNotFoundError: If the provided type ID does not exist.
        - UserSubTypeNotFoundError: If the provided subtype ID does not exist.

    """

    return BaseResponse(
        data=await service.create_user(
            **body.model_dump(), tenant_app_config=tenant_app_config
        )
    )


@router.get(
    "/self", status_code=status.HTTP_200_OK, name="Get Self", operation_id="get-Self"
)
async def get_self(
    user: Annotated[Users, Depends(current_user)],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[UserResponse]:
    """
    Retrieves the profile information of the currently authenticated user.

    Args:
        - tenant_key (int/str): The tenant_key means tenant_id or name.
        This is required.
        - app_key (int/str): The app_key means app_id or name. This is required.

    Returns:
        - BaseResponse[UserResponse]: A response containing
        the user's profile information.

    Raises:
        - UserNotFoundError: If no user with the provided username is found.

    """

    return BaseResponse(data=await service.get_self(user_id=user.id))


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    name="Get all users",
    operation_id="get-all-users",
)
async def get_all_users(
    param: Annotated[Params, Depends()],
    service: Annotated[UserService, Depends()],
    user: Annotated[Users, Depends(current_user)],
    user_ids: Annotated[list[int] | None, Query()] = None,
    username: Annotated[str | None, Query()] = None,
    email: Annotated[str | None, Query()] = None,
    phone: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    type_name: Annotated[str | None, Query(alias="type")] = None,
    sub_type: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    sortby: Annotated[UserSortBy | None, Query()] = None,
) -> BaseResponse[Page[ListUserResponse]]:
    """
    Retrieves a paginated list of users with optional filtering and sorting.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - param (Params): Pagination parameters including page number and size.
      - user_ids (list[int] | None): Optional list of user IDs to filter.
      - username (str | None): Optional filter by username.
      - email (str | None): Optional filter by email address.
      - phone (str | None): Optional filter by phone number.
      - role (str | None): Optional filter by user role.
      - type_name (str | None): Optional filter by user type.
      - sub_type (str | None): Optional filter by user sub_type.
      - is_active (bool | None): Optional filter by active status.
      - sortby (UserSortBy | None): Optional sorting field and direction.

    Returns:
      - BaseResponse[Page[ListUserResponse]]: A paginated response containing
        a list of users matching the provided criteria.

    Raises:
      - UserNotFoundError: If no user with the provided username is found.

    """

    return BaseResponse(
        data=await service.get_all_users(
            page_param=param,
            user=user,
            user_ids=user_ids,
            username=username,
            email=email,
            phone=phone,
            role_name=role,
            type_name=type_name,
            sub_type_name=sub_type,
            is_active=is_active,
            sortby=sortby,
        )
    )


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="Get user by id",
    operation_id="get-user-by-id",
)
async def get_user_by_id(
    user_id: Annotated[int, Path()], service: Annotated[UserService, Depends()]
) -> BaseResponse[ListUserResponse]:
    """
    Retrieves detailed information about a specific user by their ID.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - user_id (int): The unique identifier of the user to retrieve.

    Returns:
      - BaseResponse[ListUserResponse]: A response containing the user's information.

    Raises:
      - UserNotFoundError: If no user with the provided username is found.

    """

    return BaseResponse(data=await service.get_user_by_id(user_id=user_id))


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="Update user",
    operation_id="update-user",
)
async def update_user(
    body: Annotated[BaseUserRequest, Body()],
    user_id: Annotated[int, Path()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[UpdateUserResponse]:
    """
    Updates the information of a specific user by their ID.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - user_id (int): The unique identifier of the user to retrieve.
      - username (str | None): The username of the user.
      - phone (str | None): The phone number of the user.
      - email (str | None): The email address of the user.
      - role_ids (list[int] | None) : List of role IDs to assign to the user.
      - type_id (int | None) : The Type ID of the user.
      - subtype_id (int | None) : The Subtype ID of the user.
      - password (str | None): The password of the user.

    Returns:
      - BaseResponse[UpdateUserResponse]: A response containing the updated user data.

    Raises:
      - UserNotFoundError: If no user with the provided username is found.
      - PhoneAlreadyExistsError: If the provided phone number already exists.
      - EmailAlreadyExistsError: If the provided email address already exists.
      - RoleNotFoundError: If the provided role ID does not exist.
      - UserTypeNotFoundError: If the provided user type ID does not exist.
      - UserSubtypeNotFoundError: If the provided user subtype ID does not exist.

    """

    return BaseResponse(data=await service.update(user_id=user_id, **body.model_dump()))


@router.patch(
    "/{user_id}/status",
    name="Make user active/Inactive",
    operation_id="change-user-status",
    status_code=status.HTTP_200_OK,
)
async def change_user_status(
    user_id: Annotated[int, Path()], service: Annotated[UserService, Depends()]
) -> BaseResponse[UserStatusResponse]:
    """
    Toggles the active status of a user by their ID.

    Args:
        - tenant_key (int/str): The tenant_key means tenant_id or name.
        This is required.
        - app_key (int/str): The app_key means app_id or name. This is required.
        - user_id (int): The ID of the user whose status is to be changed.

    Returns:
        - BaseResponse[UserStatusResponse]: A response indicating
        the user's updated status.

    Raises:
        - UserNotFoundError: If no user with the provided username is found.

    """

    return BaseResponse(data=await service.change_user_status(user_id=user_id))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="delete user",
    operation_id="delete-user",
)
async def delete_user(
    user_id: Annotated[int, Path()], service: Annotated[UserService, Depends()]
) -> BaseResponse[SuccessResponse]:
    """
    Deletes a user account by their ID.

    Args:
        - tenant_key (int/str): The tenant_key means tenant_id or name.
        This is required.
        - app_key (int/str): The app_key means app_id or name. This is required.
        - user_id (int): The ID of the user whose status is to be changed.

    Returns:
        - BaseResponse[SuccessResponse]: A response indicating successful deletion of
        the user.

    Raises:
        - UserNotFoundError: If no user with the provided username is found.
    """
    return BaseResponse(data=await service.delete(user_id=user_id))


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    name="Reset Password",
    operation_id="reset-password",
)
async def reset_password(
    body: Annotated[ResetPasswordRequest, Body()],
    service: Annotated[UserService, Depends()],
    tenant_app_config: Annotated[TenantAppConfig, Depends(get_tenant_app_config)],
) -> BaseResponse[SuccessResponse]:
    """
    Resets the password for a user based on the provided user ID and new password.

     Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - email (str): The email of the user (optional).
      - phone (str): The phone number of the user (optional).
      - password (str): The new password to be set.
      - confirm_password (str): The confirmation of the new password.

     Returns:
      - BaseResponse[SuccessResponse]: A response indicating the success of
      the password reset operation.

     Raises:
      - UserNotFoundError: If no user with the provided phone number is found.
      - WeakPasswordError: If the provided password is weak.
      - PasswordNotMatchError: If the new password and confirmation
      password do not match.
      - PasswordMatchedError: If the new password is the same as the last five password.
    """

    return BaseResponse(
        data=await service.reset_password(
            phone=body.phone,
            email=body.email,
            password=body.password,
            tenant_app_config=tenant_app_config,
        )
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    name="Change Password",
    operation_id="change-password",
)
async def change_password(
    body: Annotated[ChangePasswordRequest, Body()],
    service: Annotated[UserService, Depends()],
    token_claims: Annotated[dict[str, Any], Depends(verify_change_password_token)],
    tenant_app_config: Annotated[TenantAppConfig, Depends(get_tenant_app_config)],
) -> BaseResponse[SuccessResponse]:
    """
    Changes the password for the currently authenticated user.
    Args:
        - tenant_key (int/str): The tenant_key means tenant_id or name.This is required.
        - app_key (int/str): The app_key means app_id or name. This is required.
        - current_password (str): The current password of the user.
        - new_password (str): The new password to be set.
        - user_id (int): The ID of the user whose password is to be changed.

    Returns:
        - BaseResponse[SuccessResponse]: A response indicating whether
        the password was successfully changed.

    Raises:
        - UserNotFoundError: If no user with the provided username is found.
        - InvalidPasswordError:  If the provided current password is invalid.
        - PasswordMatchedError:  If the new password is the same as
        the last five password.
        - PasswordNotMatchError: If the new password and confirmation
        password do not match.

    """
    user_id = int(token_claims.get("sub"))
    return BaseResponse(
        data=await service.change_password(
            user_id=user_id, **body.model_dump(), tenant_app_config=tenant_app_config
        )
    )


@router.post(
    "/generate-otp",
    status_code=status.HTTP_200_OK,
    name="Generate OTP",
    operation_id="generate-otp",
)
async def generate_otp(
    body: Annotated[GenerateOTPRequest, Body()],
    service: Annotated[UserService, Depends()],
    app_config: Annotated[TenantAppConfig, Depends(get_tenant_app_config)],
) -> BaseResponse[GenerateOTPResponse]:
    """
    Generates a One-Time Password (OTP) for user login.

    Args:
        - tenant_key (int/str): The tenant_key means tenant_id or name.
        This is required.
        - app_key (int/str): The app_key means app_id or name. This is required.

    Returns:
        - SuccessResponse : A response indicating whether the OTP was
        successfully generated.

    Raises:
        - UserNotFoundError: If no user with the provided phone number is found.
    """

    return BaseResponse(
        data=await service.generate_user_otp(**body.model_dump(), app_config=app_config)
    )


@router.post(
    "/mfa/setup",
    status_code=status.HTTP_200_OK,
    name="Setup MFA",
    description="Setup MFA",
    operation_id="setup-mfa",
)
async def setup_mfa(
    claims: Annotated[dict[str, str], Depends(verify_mfa_setup_token)],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[MFASetupResponse]:
    """Verify OTP for user login."""
    return BaseResponse(data=await service.setup_user_mfa(user_id=int(claims["sub"])))


@router.post(
    "/mfa/verify",
    status_code=status.HTTP_200_OK,
    name="Verify MFA",
    description="Verify MFA",
    operation_id="verify-mfa",
)
async def verify_mfa(
    claims: Annotated[dict[str, str], Depends(verify_mfa_verification_token)],
    body: Annotated[VerifyMFARequest, Body()],
    service: Annotated[UserService, Depends()],
    request: Request,
) -> BaseResponse[MFAVerifiedResponse]:
    """Verify MFA for user login."""
    return BaseResponse(
        data=await service.verify_user_mfa(
            **body.model_dump(), user_id=int(claims["sub"]), request=request
        )
    )


@router.post(
    "/mfa/reset",
    status_code=status.HTTP_200_OK,
    name="Reset MFA",
    description="Reset MFA",
    operation_id="reset-mfa",
)
async def reset_mfa(
    claims: Annotated[dict[str, str], Depends(verify_mfa_verification_token)],
    body: Annotated[ResetMFARequest, Body()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[MFAResetResponse]:
    """Reset MFA for user login."""
    return BaseResponse(
        data=await service.reset_user_mfa(
            user_id=int(claims["sub"]), **body.model_dump()
        )
    )


@router.patch(
    "/mfa/enable",
    status_code=status.HTTP_200_OK,
    name="Enable MFA",
    description="Enable MFA",
    operation_id="enable-mfa",
)
async def enable_mfa(
    claims: Annotated[dict[str, str], Depends(verify_access_token)],
    body: Annotated[EnableMFARequest, Body()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[MFAEnableResponse]:
    """Enable MFA for user login."""
    return BaseResponse(
        data=await service.enable_user_mfa(
            user_id=int(claims["sub"]), **body.model_dump()
        )
    )


@router.patch(
    "/mfa/disable",
    status_code=status.HTTP_200_OK,
    name="Disable MFA",
    description="Disable MFA",
    operation_id="disable-mfa",
)
async def disable_mfa(
    claims: Annotated[dict[str, str], Depends(verify_access_token)],
    body: Annotated[DisableMFARequest, Body()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """Disable MFA for user login."""
    return BaseResponse(
        data=await service.disable_user_mfa(
            user_id=int(claims["sub"]), **body.model_dump()
        )
    )
