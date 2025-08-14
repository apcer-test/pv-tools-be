"""Controller for user."""

import logging
from typing import Annotated

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Body, Depends, Path, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi_pagination import Page, Params

from apps.users.constants import UserSortBy
from apps.users.models.user import Users
from apps.users.schemas.request import (
    AssignUserClientsRequest,
    CreateUserRequest,
    UpdateUserRequest,
)
from apps.users.schemas.response import (
    AssignUserClientsResponse,
    CreateUserResponse,
    ListUserResponse,
    UpdateUserResponse,
    UserResponse,
    UserStatusResponse,
)
from apps.users.services import MicrosoftSSOService, UserService
from apps.users.utils import current_user, permission_required
from config import AppEnvironment, settings
from constants.config import MICROSOFT_GENERATE_CODE_SCOPE
from core.types import Providers
from core.utils.schema import BaseResponse, SuccessResponse
from core.utils.sso_client import SSOOAuthClient

router = APIRouter(prefix="/users", tags=["User"])

logger = logging.getLogger(__name__)


@router.get(
    "/self", status_code=status.HTTP_200_OK, name="Get Self", operation_id="get-Self"
)
async def get_self(
    user: Annotated[tuple[Users, str], Depends(current_user)],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[UserResponse]:
    """
    Retrieves the profile information of the currently authenticated user.

    Args:
        - client_slug (str): The client slug means client_id or name. This is required.

    Returns:
        - BaseResponse[UserResponse]: A response containing
        the user's profile information.

    Raises:
        - UserNotFoundError: If no user with the provided username is found.

    """

    return BaseResponse(
        data=await service.get_self(
            client_id=user.get("client_id"), user_id=user.get("user").id
        )
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    name="Get all users",
    operation_id="get-all-users",
    dependencies=[Depends(permission_required(["user"], ["user-management"]))],
)
async def get_all_users(
    param: Annotated[Params, Depends()],
    service: Annotated[UserService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
    user_ids: Annotated[list[str] | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    user_type: Annotated[str | None, Query()] = None,
    client: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    sortby: Annotated[UserSortBy | None, Query()] = None,
) -> BaseResponse[Page[ListUserResponse]]:
    """
    Retrieves a paginated list of users with optional filtering and sorting.

    Args:
      - client_slug (str): The client slug means client_id or name. This is required.
      - param (Params): Pagination parameters including page number and size.
      - user_ids (list[str] | None): Optional list of user IDs to filter.
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
            client_id=user.get("client_id"),
            page_param=param,
            user=user.get("user").id,
            user_ids=user_ids,
            search=search,
            role_slug=role,
            user_type_slug=user_type,
            client_slug=client,
            is_active=is_active,
            sortby=sortby,
        )
    )


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="Get user by id",
    operation_id="get-user-by-id",
    dependencies=[Depends(permission_required(["user"], ["user-management"]))],
)
async def get_user_by_id(
    user: Annotated[tuple[Users, str], Depends(current_user)],
    user_id: Annotated[str, Path()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[ListUserResponse]:
    """
    Retrieves detailed information about a specific user by their ID.

    Args:
      - client_slug (str): The client slug means client_id or name. This is required.
      - user_id (str): The unique identifier of the user to retrieve.

    Returns:
      - BaseResponse[ListUserResponse]: A response containing the user's information.

    Raises:
      - UserNotFoundError: If no user with the provided username is found.

    """

    return BaseResponse(
        data=await service.get_user_by_id(
            client_id=user.get("client_id"), user_id=user_id
        )
    )


@router.get(
    "/openid/login/{provider}/{client_id}",
    status_code=status.HTTP_200_OK,
    response_description="",
    name="login",
    description="endpoint for login using provider",
    operation_id="sso_login",
)
async def login_by_provider(
    request: Request,
    provider: Annotated[Providers, Path()],
    client_id: Annotated[str, Path()],
) -> RedirectResponse:
    """
    Open api provider login function
    """
    try:
        match provider:
            case Providers.MICROSOFT:
                if settings.ENV == AppEnvironment.LOCAL:
                    redirect_uri = request.url_for(
                        "sso_auth_callback", provider=provider.value
                    )
                else:
                    redirect_uri = f"{settings.SOCIAL_AUTH_REDIRECT_URL}/{settings.SOCIAL_AUTH_ENDPOINT}/{provider}"
                redirect_uri = f"{redirect_uri}?client_slug={client_id}"
                return (
                    await SSOOAuthClient(provider.value)
                    .oauth.create_client(provider.value)
                    .authorize_redirect(request, redirect_uri)
                )
            case _:
                return RedirectResponse(url=settings.UI_LOGIN_SCREEN)
    except Exception as e:
        logger.error(f"SSO login error for provider {provider}: {str(e)}")
        return RedirectResponse(url=settings.UI_LOGIN_SCREEN)


@router.get(
    "/{provider}",
    status_code=status.HTTP_200_OK,
    name="sso_auth_callback",
    description="callback endpoint for auth using provider",
    operation_id="sso_auth_callback",
)
async def auth(
    request: Request,
    client_slug: Annotated[str, Query()],
    service: Annotated[MicrosoftSSOService, Depends()],
    provider: Annotated[Providers, Path()],
) -> RedirectResponse:
    """
    get details by provider
    """
    try:
        match provider:
            case Providers.MICROSOFT:
                try:
                    user_data = {}
                    # Get access token
                    token = (
                        await SSOOAuthClient(provider.value)
                        .oauth.create_client(provider.value)
                        .authorize_access_token(request)
                    )
                    if not token:
                        logger.error("Failed to get access token from Microsoft")
                        return RedirectResponse(url=settings.UI_LOGIN_SCREEN)

                    # Get ID token claims
                    user_data.update(
                        await SSOOAuthClient(provider.value)
                        .oauth.create_client(provider.value)
                        .parse_id_token(token, nonce=request.session.get("nonce"))
                    )

                    # Get user info
                    user_data.update(
                        await SSOOAuthClient(provider.value)
                        .oauth.create_client(provider.value)
                        .userinfo(token=token)
                    )

                    logger.info(
                        f"Successfully got user data from Microsoft: {user_data.get('email')}"
                    )
                    return await service.sso_user(
                        token=token.get("id_token"),
                        client_slug=client_slug,
                        **user_data,
                    )

                except OAuthError as oauth_error:
                    logger.error(
                        f"OAuth error during Microsoft callback: {str(oauth_error)}"
                    )
                    return RedirectResponse(url=settings.UI_LOGIN_SCREEN)
                except Exception as e:
                    logger.error(
                        f"Unexpected error during Microsoft callback: {str(e)}"
                    )
                    return RedirectResponse(url=settings.UI_LOGIN_SCREEN)
                finally:
                    # Clean up session
                    request.session.clear()

            case _:
                logger.warning(f"Unsupported provider in callback: {provider}")
                return RedirectResponse(url=settings.UI_LOGIN_SCREEN)
    except Exception as e:
        logger.error(f"Global error in auth callback: {str(e)}")
        return RedirectResponse(url=settings.UI_LOGIN_SCREEN)


@router.get(
    "/auth/generate-code",
    status_code=status.HTTP_200_OK,
    response_description="",
    name="generate code",
    description="endpoint for generate code",
    operation_id="generate_code",
)
async def generate_code(request: Request) -> RedirectResponse:
    """
    Open api generate code function
    """

    url = f"{settings.MICROSOFT_BASE_URL}/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?client_id={settings.MICROSOFT_CLIENT_ID}&response_type=code&redirect_uri={settings.GENERATE_CODE_REDIRECT_URL}&response_mode=query&scope={MICROSOFT_GENERATE_CODE_SCOPE}&state=12345&sso_reload=true"
    return RedirectResponse(url=url)


@router.get(
    "/auth/generate-code/callback",
    status_code=status.HTTP_200_OK,
    name="generate code callback",
    description="callback endpoint for generate code",
    operation_id="generate_code_callback",
)
async def generate_code_callback(request: Request) -> RedirectResponse:
    """
    get details by generate code callback
    """
    code = request.query_params.get("code")
    return RedirectResponse(url=settings.CODE_REDIRECT_URL + f"?code={code}")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create User",
    operation_id="create-user",
    dependencies=[Depends(permission_required(["user"], ["user-management"]))],
)
async def create_user(
    body: Annotated[CreateUserRequest, Body()],
    service: Annotated[UserService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[CreateUserResponse]:
    """
    Creates a new user with basic information.

    Args:
        - first_name (str): The user's first name.
        - last_name (str): The user's last name.
        - phone (str): The user's phone number.
        - email (str): The user's email address.
        - reporting_manager_id (str | None): The user's reporting manager ID.

    Returns:
        - BaseResponse[CreateUserResponse]: A response containing the created user's basic information.

    Raises:
        - PhoneAlreadyExistsError: If the provided phone number already exists.
        - EmailAlreadyExistsError: If the provided email address already exists.

    """

    return BaseResponse(
        data=await service.create_simple_user(
            **body.model_dump(), user_id=user.get("user").id
        )
    )


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="Update user",
    operation_id="update-user",
    dependencies=[Depends(permission_required(["user"], ["user-management"]))],
)
async def update_user(
    user: Annotated[tuple[Users, str], Depends(current_user)],
    body: Annotated[UpdateUserRequest, Body()],
    user_id: Annotated[str, Path()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[UpdateUserResponse]:
    """
    Updates the information of a specific user by their ID.

    Args:
      - user_id (str): The unique identifier of the user to retrieve.
      - first_name (str | None): The user's first name.
      - last_name (str | None): The user's last name.
      - phone (str | None): The user's phone number.
      - email (str | None): The user's email address.
      - reporting_manager_id (str | None): The user's reporting manager ID.
      - reason (str): The reason for the update (required).

    Returns:
      - BaseResponse[UpdateUserResponse]: A response containing the updated user data.

    Raises:
      - UserNotFoundError: If no user with the provided ID is found.
      - PhoneAlreadyExistsError: If the provided phone number already exists.
      - EmailAlreadyExistsError: If the provided email address already exists.

    """

    return BaseResponse(
        data=await service.update_simple_user(
            user_id=user_id, **body.model_dump(), current_user_id=user.get("user").id
        )
    )


@router.post(
    "/{user_id}/assign-clients",
    status_code=status.HTTP_200_OK,
    name="Assign clients to user",
    operation_id="assign-user-clients",
    dependencies=[Depends(permission_required(["user"], ["user-management"]))],
)
async def assign_user_clients(
    user: Annotated[tuple[Users, str], Depends(current_user)],
    body: Annotated[AssignUserClientsRequest, Body()],
    user_id: Annotated[str, Path()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[AssignUserClientsResponse]:
    """
    Assigns clients, roles, and user types to a user.

    Args:
        - user_id (str): The ID of the user to assign clients to.
        - assignments (list[UserClientAssignment]): List of client assignments with role and user type.

    Returns:
        - BaseResponse[AssignUserClientsResponse]: A response containing the assignment results.

    Raises:
        - UserNotFoundError: If no user with the provided ID is found.
        - RoleNotFoundError: If any of the provided role IDs do not exist.
        - UserTypeNotFoundError: If any of the provided user type IDs do not exist.

    """

    return BaseResponse(
        data=await service.assign_user_clients(
            user_id=user_id,
            assignments=body.assignments,
            current_user_id=user.get("user").id,
        )
    )


@router.patch(
    "/{user_id}/status",
    name="Make user active/Inactive",
    operation_id="change-user-status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(permission_required(["user"], ["user-management"]))],
)
async def change_user_status(
    user: Annotated[tuple[Users, str], Depends(current_user)],
    user_id: Annotated[str, Path()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[UserStatusResponse]:
    """
    Toggles the active status of a user by their ID.

    Args:
        - client_slug (str): The client slug means client_id or name. This is required.
        - user_id (str): The ID of the user whose status is to be changed.

    Returns:
        - BaseResponse[UserStatusResponse]: A response indicating
        the user's updated status.

    Raises:
        - UserNotFoundError: If no user with the provided username is found.

    """

    return BaseResponse(
        data=await service.change_user_status(
            client_id=user.get("client_id"), user_id=user_id
        )
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="delete user",
    operation_id="delete-user",
    dependencies=[Depends(permission_required(["user"], ["user-management"]))],
)
async def delete_user(
    user: Annotated[tuple[Users, str], Depends(current_user)],
    user_id: Annotated[str, Path()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """
    Deletes a user account by their ID.

    Args:
        - client_slug (str): The client slug means client_id or name. This is required.
        - user_id (str): The ID of the user whose status is to be changed.

    Returns:
        - BaseResponse[SuccessResponse]: A response indicating successful deletion of
        the user.

    Raises:
        - UserNotFoundError: If no user with the provided username is found.
    """
    return BaseResponse(
        data=await service.delete(client_id=user.get("client_id"), user_id=user_id)
    )
