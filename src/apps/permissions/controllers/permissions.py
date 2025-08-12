"""routes for permission operations."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi_pagination import Page, Params

from apps.permissions.constants import PermissionSortBy
from apps.permissions.schemas.request import CreatePermissionRequest
from apps.permissions.schemas.response import BasePermissionResponse
from apps.permissions.services.permissions import PermissionService
from core.constants import SortType
from core.dependencies import verify_api_keys
from core.utils.schema import BaseResponse, SuccessResponse

router = APIRouter(
    prefix="/{tenant_key}/{app_key}/permissions",
    tags=["Permissions"],
    dependencies=[Depends(verify_api_keys)],
)


@router.post("", status_code=status.HTTP_201_CREATED, name="Create permission")
async def create_permission(
    body: Annotated[CreatePermissionRequest, Body()],
    service: Annotated[PermissionService, Depends()],
) -> BaseResponse[BasePermissionResponse]:
    """
    Create a new permission.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app key means app_id or name. This is required.
      - name (str): The name of the permission. This is required.
      - slug (str): The slug of the permission. This is optional.

    Returns:
      - BaseResponse[BasePermissionResponse]: The newly created permission wrapped in a base response.

    Raises:
      - PermissionAlreadyExistsError: If a permission with the same name already exists.
    """

    return BaseResponse(data=await service.create_permission(**body.model_dump()))


@router.get("", status_code=status.HTTP_200_OK, name="Get all permissions")
async def get_all_permissions(
    service: Annotated[PermissionService, Depends()],
    params: Annotated[Params, Depends()],
    sort_by: Annotated[PermissionSortBy | None, Query()] = None,
    sort_type: Annotated[SortType | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> BaseResponse[Page[BasePermissionResponse]]:
    """
    Retrieve a paginated list of all permissions.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app key means app_id or name. This is required.
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
            params=params, sort_by=sort_by, sort_type=sort_type, search=search
        )
    )


@router.get(
    "/{permission_key}", status_code=status.HTTP_200_OK, name="Get permission by key"
)
async def get_permission_by_id(
    permission_key: Annotated[int | str, Path()],
    service: Annotated[PermissionService, Depends()],
) -> BaseResponse[BasePermissionResponse]:
    """
    Retrieve a permission by its unique permission_key(ID/Name).

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app key means app_id or name. This is required.
      - permission_key (int | str): The unique identifier (ID/Name) of the permission.

    Returns:
      - BaseResponse[BasePermissionResponse]: The permission details wrapped in a base response.

    Raises:
      - PermissionNotFoundError: If no permission is found with the given key.
    """

    return BaseResponse(
        data=await service.get_permission_by_id(permission_key=permission_key)
    )


@router.put(
    "/{permission_key}", status_code=status.HTTP_200_OK, name="Update permission"
)
async def update_permission(
    permission_key: Annotated[int | str, Path()],
    body: Annotated[CreatePermissionRequest, Body()],
    service: Annotated[PermissionService, Depends()],
) -> BaseResponse[BasePermissionResponse]:
    """
    Update an existing permission.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app key means app_id or name. This is required.
      - permission_key (int | str): The unique identifier (ID or key) of the permission to update.
      - name (str): The name of the permission. This is required.
      - slug (str): The slug of the permission. This is optional.

    Returns:
      - BaseResponse[BasePermissionResponse]: The updated permission wrapped in a base response.

    Raises:
      - PermissionNotFoundError: If no permission is found with the given key.
    """

    return BaseResponse(
        data=await service.update_permission(
            permission_key=permission_key, **body.model_dump()
        )
    )


@router.delete(
    "/{permission_key}",
    status_code=status.HTTP_200_OK,
    name="delete permission using permission_key",
)
async def delete_permission(
    permission_key: Annotated[int | str, Path()],
    service: Annotated[PermissionService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """
    Delete a permission by its unique permission_key.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app key means app_id or name. This is required.
      - permission_key (int | str): The unique identifier (ID or key) of the permission to delete.

    Returns:
      - BaseResponse[SuccessResponse]: A success message wrapped in a base response upon successful deletion.

    Raises:
      - PermissionNotFoundError: If no permission is found with the given key.
      - PermissionAssignedFoundError: If a permission assigned to user found.
    """

    return BaseResponse(
        data=await service.delete_permission(permission_key=permission_key)
    )
