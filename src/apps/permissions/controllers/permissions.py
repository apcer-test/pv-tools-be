"""routes for permission operations."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi_pagination import Page, Params

from apps.permissions.constants import PermissionSortBy
from apps.permissions.schemas.request import CreatePermissionRequest, UpdatePermissionRequest
from apps.permissions.schemas.response import BasePermissionResponse
from apps.permissions.services.permissions import PermissionService
from apps.users.models.user import Users
from apps.users.utils import current_user
from core.constants import SortType
from core.utils.schema import BaseResponse, SuccessResponse

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


@router.post("", status_code=status.HTTP_201_CREATED, name="Create permission")
async def create_permission(
    body: Annotated[CreatePermissionRequest, Body()],
    service: Annotated[PermissionService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[BasePermissionResponse]:
    """
    Create a new permission.

    Args:
      - name (str): The name of the permission. This is required.

    Returns:
      - BaseResponse[BasePermissionResponse]: The newly created permission wrapped in a base response.

    Raises:
      - PermissionAlreadyExistsError: If a permission with the same name already exists.
    """

    return BaseResponse(data=await service.create_permission(**body.model_dump(), client_id=user.get("client_id"), user_id=user.get("user").id))


@router.get("", status_code=status.HTTP_200_OK, name="Get all permissions")
async def get_all_permissions(
    params: Annotated[Params, Depends()],
    service: Annotated[PermissionService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
    sort_by: Annotated[PermissionSortBy | None, Query()] = None,
    sort_type: Annotated[SortType | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> BaseResponse[Page[BasePermissionResponse]]:
    """
    Retrieve a paginated list of all permissions.

    Args:
      - params (Params): Pagination parameters including page number and size.
      - sort_by (PermissionSortBy | None): Field to sort the results by. Optional.
      - sort_type (SortType | None): Sorting order (asc or desc). Optional.
      - search (str | None): Search term to filter permissions by name. Optional.

    Returns:
      - BaseResponse[Page[BasePermissionResponse]]: A paginated list of permissions wrapped in a base response.

    Raises:
      - PermissionNotFoundError: If a permission with the same name not exists.

    """
    
    return BaseResponse(
        data=await service.get_all_permissions(
            params=params, sort_by=sort_by, sort_type=sort_type, search=search, client_id=user.get("client_id")
        )
    )


@router.put(
    "/{permission_key}", status_code=status.HTTP_200_OK, name="Update permission"
)
async def update_permission(
    permission_key: Annotated[int | str, Path()],
    body: Annotated[UpdatePermissionRequest, Body()],
    service: Annotated[PermissionService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[BasePermissionResponse]:
    """
    Update an existing permission.

    Args:
      - permission_key (int | str): The unique identifier (ID or key) of the permission to update.
      - name (str): The name of the permission. This is required.
      - slug (str | None): Optional slug for the permission.
      - description (str | None): Optional description for the permission.
      - permission_metadata (dict | None): Optional metadata for the permission.

    Returns:
      - BaseResponse[BasePermissionResponse]: The updated permission wrapped in a base response.

    Raises:
      - PermissionNotFoundError: If no permission is found with the given key.
    """

    return BaseResponse(
        data=await service.update_permission(
            permission_key=permission_key, **body.model_dump(), client_id=user.get("client_id"), user_id=user.get("user").id
        )
    )
