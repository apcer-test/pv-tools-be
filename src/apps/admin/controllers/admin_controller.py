from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, Query, Request, status
from fastapi.responses import JSONResponse

import constants
from apps.admin.schemas.admin_user_response import AdminListUsersResponse
from apps.admin.schemas.request import EncryptedRequest
from apps.admin.services.user import AdminUserService
from apps.user.models.user import UserModel
from apps.user.schemas.response import BaseUserResponse
from core.auth import AdminHasPermission
from core.exceptions import UnauthorizedError
from core.types import RoleType
from core.utils.pagination import PaginatedResponse, PaginationParams
from core.utils.schema import BaseResponse
from core.utils.set_cookies import set_auth_cookies

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post(
    "/sign-in",
    status_code=status.HTTP_200_OK,
    name="sign-in",
    description="sign-in",
    operation_id="sign_in_admin",
)
async def sign_in(
    request: Request,
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[AdminUserService, Depends()],
) -> JSONResponse:
    """
    Authenticate an admin user and generate access tokens.

    This endpoint handles admin login with encrypted credentials. Upon successful
    authentication, it returns access tokens and sets authentication cookies.

    Args:
        request: The FastAPI request object containing application state
        body: Encrypted request containing admin credentials
        service: AdminUserService instance for business logic

    Returns:
        JSONResponse: Response with authentication tokens and cookies

    Raises:
        InvalidCredentialsException: If credentials are invalid
        BadRequestError: If required fields are missing
    """
    res = await service.login_admin(request=request, **body.model_dump())
    if "access_token" in res and res.get("access_token"):
        data = {"status": constants.SUCCESS, "code": status.HTTP_200_OK, "data": res}
        response = JSONResponse(content=data)
        response = set_auth_cookies(response, res, RoleType.ADMIN)
        return response
    else:
        # Handle case where login fails but doesn't raise an exception
        raise UnauthorizedError(constants.UNAUTHORIZED)


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    # dependencies=[Depends(AdminHasPermission())],
    name="Admin get all users",
    description="Admin get all users with advanced pagination, search, filtering, and sorting",
    operation_id="admin_get_users",
)
async def get_users(
    service: Annotated[AdminUserService, Depends()],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(
        None, description="Search term across first_name, last_name, email, phone"
    ),
    sort_by: Optional[str] = Query(
        None,
        description="Sort field (first_name, last_name, email, created_at, updated_at)",
    ),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    filters: Optional[str] = Query(
        None, description="JSON filters: {'role': 'ADMIN', 'created_by': 'uuid'}"
    ),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
) -> BaseResponse[PaginatedResponse[AdminListUsersResponse]]:
    """
    Retrieve a paginated list of all users for admin management with advanced features.

    This endpoint allows administrators to view all registered users with:
    - Pagination support
    - Search across first_name, last_name, email, and phone
    - Filtering by role, is_active, created_by, updated_by
    - Sorting by first_name, last_name, email, created_at, updated_at
    - Date range filtering on created_at
    - Soft delete handling

    Args:
        pagination_params: Advanced pagination parameters including search, filters, and sorting
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[PaginatedResponse[AdminListUsersResponse]]: Enhanced paginated list of users

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    pagination_params = PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        filters=filters,
        date_from=date_from,
        date_to=date_to,
    )
    return BaseResponse(data=await service.get_users_advanced(params=pagination_params))


@router.get(
    "/self",
    status_code=status.HTTP_200_OK,
    name="get self",
    description="Get Self",
    operation_id="get_self_admin",
)
async def get_self_handler(
    user: Annotated[UserModel, Depends(AdminHasPermission())],
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse[BaseUserResponse]:
    """
    Retrieve the current admin user's profile information.

    This endpoint returns the authenticated admin's profile data including
    basic user information like name, email, and role.

    Args:
        user: Authenticated admin user from token
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Admin user profile data

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data=await service.get_self_admin(user_id=user.id))


@router.patch(
    "/change-password",
    name="change password",
    description="Change Password",
    operation_id="change_password",
    status_code=status.HTTP_200_OK,
)
async def change_password(
    request: Request,
    user: Annotated[UserModel, Depends(AdminHasPermission())],
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse[BaseUserResponse]:
    """
    Change the password for the authenticated admin user.

    This endpoint allows admins to update their password. The request must
    include the current password for verification and a new password that
    meets security requirements.

    Args:
        request: The FastAPI request object
        user: Authenticated admin user from token
        body: Encrypted request containing current and new passwords
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Updated admin user data

    Raises:
        InvalidCredentialsException: If current password is incorrect
        WeakPasswordException: If new password doesn't meet requirements
        UserNotFoundException: If user is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.change_password(
            request=request, **body.model_dump(), user=user.id
        )
    )
