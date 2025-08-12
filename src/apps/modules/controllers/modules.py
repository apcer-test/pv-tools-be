from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi_pagination import Page, Params

from apps.modules.constants import ModuleSortBy
from apps.modules.schemas import (
    BaseModuleResponse,
    CreateModuleRequest,
    ModuleResponse,
    UpdateModuleRequest,
)
from apps.modules.services import ModuleService
from core.constants import SortType
from core.dependencies import verify_api_keys
from core.utils.schema import BaseResponse, SuccessResponse

router = APIRouter(
    prefix="/{tenant_key}/{app_key}/modules",
    tags=["Modules"],
    dependencies=[Depends(verify_api_keys)],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create Module",
    operation_id="create_module",
)
async def create_modules(
    service: Annotated[ModuleService, Depends()],
    body: Annotated[CreateModuleRequest, Body()],
) -> BaseResponse[BaseModuleResponse]:
    """
    Create a new module.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - name (str): The name of the module.
      - slug (str | None): Optional slug for the module used for referencing or URL-friendly names.
      - parent_module_id (int | None) : Optional parent module ID to assign to the module.
      - permissions (list[int] | None): Optional list of permission IDs to assign to the module.
      - description (str | None): Optional description for the module.
      - module_metadata (dict | None): Optional JSON metadata for the module.

    Returns:
      - BaseResponse[BaseModuleResponse]: A standardized response containing the created module's information.

    Raises:
      - ModuleAlreadyExistsError: If a module with the same name already exists.
      - PermissionNotFoundError: If a permission with the given ID is not found or a permission.
    """

    return BaseResponse(data=await service.create_modules(**body.model_dump()))


@router.get(
    "", status_code=status.HTTP_200_OK, name="List Modules", operation_id="list_modules"
)
async def get_all_modules(
    service: Annotated[ModuleService, Depends()],
    params: Annotated[Params, Depends()],
    sort_by: Annotated[ModuleSortBy | None, Query()] = None,
    sort_type: Annotated[SortType | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> BaseResponse[Page[ModuleResponse]]:
    """
    Retrieve a paginated list of modules.

    Args:

      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - params (Params): Pagination parameters (page number, size, etc.).
      - sort_by (ModuleSortBy | None): Optional field name to sort the results by.
      - sort_type (SortType | None): Optional sort direction (ascending or descending).
      - search (str | None): Optional search keyword to filter modules by name or other attributes.

    Returns:
      - BaseResponse[Page[ModuleResponse]]: A standardized response containing a paginated list of modules.

    """

    return BaseResponse(
        data=await service.get_all_modules(
            params=params, sort_by=sort_by, sort_type=sort_type, search=search
        )
    )


@router.get(
    "/{module_key}",
    status_code=status.HTTP_200_OK,
    name="Get Module",
    operation_id="get_module",
)
async def get_module_by_id(
    module_key: Annotated[int | str, Path()],
    service: Annotated[ModuleService, Depends()],
) -> BaseResponse[ModuleResponse]:
    """
    Retrieve a specific module by its key.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - module_key (int | str): Unique identifier of the module (could be an ID or key).

    Returns:
      - BaseResponse[ModuleResponse]: A standardized response containing the module's details.

    Raises:
      - ModuleNotFoundError: If the module is not found.
    """

    return BaseResponse(data=await service.get_module_by_id(module_key))


@router.put(
    "/{module_key}",
    status_code=status.HTTP_200_OK,
    name="Update Module",
    operation_id="update_module",
)
async def update_module(
    module_key: Annotated[int | str, Path()],
    body: Annotated[UpdateModuleRequest, Body()],
    service: Annotated[ModuleService, Depends()],
) -> BaseResponse[ModuleResponse]:
    """
    Update an existing module.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - module_key (int | str): Unique identifier of the module to be updated.
      - name (str): The name of the module.
      - slug (str | None): Optional slug for the module used for referencing or URL-friendly names.
      - parent_module_id (int | None) : Optional parent module ID to assign to the module.
      - permissions (list[int] | None): Optional list of permission IDs to assign to the module.
      - description (str | None): Optional description for the module.
      - module_metadata (dict | None): Optional JSON metadata for the module.

    Returns:
      - BaseResponse[ModuleResponse]: A standardized response containing the updated module's information.

    Raises:
      - ModuleNotFoundError: If the module to be updated is not found.
      - ModuleAlreadyExistsError: If a module with the same name already exists.
      - PermissionNotFoundError: If a permission with the given ID is not found or a permission.
    """
    return BaseResponse(
        data=await service.update_module(module_key=module_key, **body.model_dump())
    )


@router.delete(
    "/{module_key}",
    status_code=status.HTTP_200_OK,
    name="Delete Module",
    operation_id="delete_module",
)
async def delete_module(
    module_key: Annotated[int | str, Path()],
    service: Annotated[ModuleService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """
    Delete a module by its key.

    Args:
      - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
      - app_key (int/str): The app_key means app_id or name. This is required.
      - module_key (int | str): Unique identifier of the module to be deleted.

    Returns:
      - BaseResponse[SuccessResponse]: A standardized response indicating successful deletion.

    Raises:
      - ModuleNotFoundError: If the module to be deleted is not found.
      - ModuleAssignedFoundError: If the module is assigned to any users.
    """
    return BaseResponse(data=await service.delete_module(module_key=module_key))
