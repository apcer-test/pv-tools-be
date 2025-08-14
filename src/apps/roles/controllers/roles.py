"""This module contains controllers for role management.

It provides API endpoints for creating, updating, deleting, and retrieving roles.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi_pagination import Page, Params

from apps.roles.constants import RolesSortBy
from apps.roles.schemas import BaseRoleResponse, CreateRoleRequest, UpdateRoleRequest
from apps.roles.schemas.response import RoleResponse
from apps.roles.services import RoleService
from apps.users.models.user import Users
from apps.users.utils import current_user, permission_required
from core.utils.schema import BaseResponse, SuccessResponse

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create role",
    operation_id="create-role",
    dependencies=[Depends(permission_required(["roles"], ["role-management"]))],
)
async def create_role(
    body: Annotated[CreateRoleRequest, Body()],
    service: Annotated[RoleService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[BaseRoleResponse]:
    """
    Create a new role.

    Args:
      - name (str): The name of the role (e.g., "Manager", "Editor").
      - module_permissions (list[ModulePermissionAssignment] | None):
            Optional list of module-permission assignments specifying what actions this role can perform.
      - description (str | None): Optional description for the role.
      - role_metadata (dict[str, Any] | None): Optional metadata for the role.

    Returns:
      - BaseResponse[BaseRoleResponse]: A response wrapper containing the newly created role's information.

    Raises:
      - RoleAlreadyExistsError: If a role with the same name already exists.
    """

    return BaseResponse(
        data=await service.create_role(
            **body.model_dump(),
            client_id=user.get("client_id"),
            user_id=user.get("user").id
        )
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    name="Get all roles",
    operation_id="get-all-roles",
    dependencies=[Depends(permission_required(["roles"], ["role-management"]))],
)
async def get_all_roles(
    service: Annotated[RoleService, Depends()],
    page_params: Annotated[Params, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
    sortby: Annotated[RolesSortBy | None, Query()] = None,
    name: Annotated[str | None, Query()] = None,
) -> BaseResponse[Page[BaseRoleResponse]]:
    """
    Retrieve a paginated list of all roles with optional filtering and sorting.

    Args:
      - page_params (Params): Pagination parameters, including page number and size.
      - sortby (RolesSortBy | None): Optional sorting criteria (e.g., by name or created date).
      - name (str | None): Optional filter to return roles that match the given name or partial name.

    Returns:
      - BaseResponse[Page[BaseRoleResponse]]: A paginated response containing the list of roles.

    Raises:
      - RoleNotFoundError: If the role with the given key is not found.
    """
    return BaseResponse(
        data=await service.get_all_roles(
            page_params, sortby, name, client_id=user.get("client_id")
        )
    )


@router.get(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    name="Get role by id",
    operation_id="get-role-by-key",
    dependencies=[Depends(permission_required(["roles"], ["role-management"]))],
)
async def get_role_by_id(
    role_id: Annotated[str, Path()],
    service: Annotated[RoleService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[RoleResponse]:
    """
    Retrieve a role by its key.

    Args:
      - role_id (str): The unique identifier of the role (can be a numeric ID or a string slug).

    Returns:
      - BaseResponse[RoleResponse]: The role's details wrapped in a base response format.

    Raises:
      - RoleNotFoundError: If the role with the given key is not found.
    """

    return BaseResponse(
        data=await service.get_roles_by_ids(
            role_ids=[role_id], client_id=user.get("client_id")
        )
    )


@router.put(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    name="Update role",
    operation_id="update-role",
    dependencies=[Depends(permission_required(["roles"], ["role-management"]))],
)
async def update_role(
    role_id: Annotated[str, Path()],
    body: Annotated[UpdateRoleRequest, Body()],
    service: Annotated[RoleService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[RoleResponse]:
    """
    Update a role by its key.

    Args:
      - role_id (str): The unique identifier of the role (can be a numeric ID or a string slug).
      - name (str): Optional  The name of the role (e.g., "Manager", "Editor").
      - module_permissions (list[ModulePermissionAssignment] | None):
            Optional list of module-permission assignments specifying what actions this role can perform.
      - description (str | None): Optional description for the role.
      - role_metadata (dict[str, Any] | None): Optional metadata for the role.

    Returns:
      - BaseResponse[RoleResponse]: The updated role details wrapped in a standardized response.

    Raises:
      - RoleNotFoundError: If the role with the given key is not found.
      - RoleAlreadyExistsError: If a role with the same name already exists.

    """
    return BaseResponse(
        data=await service.update_role(
            role_id=role_id,
            **body.model_dump(),
            client_id=user.get("client_id"),
            user_id=user.get("user").id
        )
    )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    name="delete role using role_id",
    operation_id="delete-role",
    dependencies=[Depends(permission_required(["roles"], ["role-management"]))],
)
async def delete_role(
    role_id: Annotated[str, Path()],
    service: Annotated[RoleService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[SuccessResponse]:
    """
    Delete a role by its key.

    Args:
      - role_slug (str): The unique identifier of the role (can be a numeric ID or a string slug).

    Returns:
      - BaseResponse[SuccessResponse]: A standardized success response indicating that the role was deleted.

    Raises:
      - RoleNotFoundError: If the role with the given key is not found.
      - RoleAssignedFoundError: If the role is assigned to any users.

    """
    return BaseResponse(
        data=await service.delete_role(
            role_id=role_id,
            client_id=user.get("client_id"),
            user_id=user.get("user").id,
        )
    )
