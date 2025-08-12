from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status
from fastapi.params import Query
from fastapi_pagination import Page, Params

from apps.user_types.constants import UserTypeSortBy
from apps.user_types.schemas.request import CreateUserTypeRequest
from apps.user_types.schemas.response import BaseUserTypeResponse
from apps.user_types.services.user_type import UserTypeService
from core.constants import SortType
from core.dependencies import verify_api_keys
from core.utils.schema import BaseResponse, SuccessResponse

router = APIRouter(
    prefix="/{tenant_key}/{app_key}/types",
    tags=["User Types"],
    dependencies=[Depends(verify_api_keys)],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create usertype",
    operation_id="create-user-type",
)
async def create_user_type(
    body: Annotated[CreateUserTypeRequest, Body()],
    service: Annotated[UserTypeService, Depends()],
) -> BaseResponse[BaseUserTypeResponse]:
    """
    Create a new user type.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app_key menas app_id or app_name. This is required..
      - name (str): The name of the user type.
      - slug (str | None): Optional slug for the user type used for referencing or URL-friendly names.

    Returns:
      - BaseResponse[BaseUserTypeResponse]: A response containing the created user type data.

    Raises:
      - UserTypeAlreadyExistsError: If a user type with the same name already exists.
    """

    return BaseResponse(data=await service.create_user_type(**body.model_dump()))


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    name="Get all user types",
    operation_id="get-all-user-types",
)
async def get_all_user_types(
    service: Annotated[UserTypeService, Depends()],
    page_params: Annotated[Params, Depends()],
    sort_by: Annotated[UserTypeSortBy | None, Query()] = None,
    sort_type: Annotated[SortType | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> BaseResponse[Page[BaseUserTypeResponse]]:
    """
    Retrieve a paginated list of user types with optional sorting and searching.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app_key menas app_id or app_name. This is required..
      - page_params (Params): Pagination parameters like page number and size.
      - sort_by (UserTypeSortBy | None): Field by which to sort the results.
      - sort_type (SortType | None): Sort order, either ascending or descending.
      - search (str | None): Keyword to filter user types by name or description.

    Returns:
      - BaseResponse[Page[BaseUserTypeResponse]]: A paginated response containing the list of user types wrapped in a BaseResponse.
    """

    return BaseResponse(
        data=await service.get_all_user_types(
            page_params=page_params, sort_by=sort_by, sort_type=sort_type, search=search
        )
    )


@router.get(
    "/{type_key}",
    status_code=status.HTTP_200_OK,
    name="Get user_type by id",
    operation_id="get-user-type-by-id",
)
async def get_user_type_by_id(
    type_key: Annotated[int | str, Path()],
    service: Annotated[UserTypeService, Depends()],
) -> BaseResponse[BaseUserTypeResponse]:
    """
    Retrieve a specific user type by its key.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app_key menas app_id or app_name. This is required..
      - type_key (int | str): The unique identifier (ID or key) of the user type.

    Returns:
      - BaseResponse[BaseUserTypeResponse]: A response containing the user type data wrapped in a BaseResponse.

    Raises:
      - UserTypeNotFoundError: If a type with the specified id not found.
    """

    return BaseResponse(data=await service.get_user_type_by_id(type_key=type_key))


@router.put(
    "/{type_key}",
    status_code=status.HTTP_200_OK,
    name="Update usertype",
    operation_id="update-usertype",
)
async def update_user_type(
    type_key: Annotated[int | str, Path()],
    body: Annotated[CreateUserTypeRequest, Body()],
    service: Annotated[UserTypeService, Depends()],
) -> BaseResponse[BaseUserTypeResponse]:
    """
    Update an existing user type.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app_key menas app_id or app_name. This is required..
      - type_key (int | str): The unique identifier (ID or key) of the user type to update.
      - name (str): The updated name of the user type.
      - slug (str | None): Optional slug for the user type used for referencing or URL-friendly names.

    Returns:
      - BaseResponse[BaseUserTypeResponse]: A response containing the updated user type data.

    Raises:
      - UserTypeNotFoundError: If a type with the specified id not found.
    """

    return BaseResponse(
        data=await service.update_user_type(type_key=type_key, **body.model_dump())
    )


@router.delete(
    "/{type_key}",
    status_code=status.HTTP_200_OK,
    name="delete usertype using user_type_id",
    operation_id="delete-usertype",
)
async def delete_user_type(
    type_key: Annotated[int | str, Path()],
    service: Annotated[UserTypeService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """
    Delete a user type by its ID or key.

    Args:
      - tenant_key (int/str): The tenant key means tenant_id or name. This is required.
      - app_key (int/str): The app_key menas app_id or app_name. This is required..
      - type_key (int | str): The unique identifier (ID or key) of the user type to delete.

    Returns:
      - BaseResponse[SuccessResponse]: A success message confirming deletion.

    Raises:
      - UserTypeNotFoundError: If a type with the specified id not found.
      - UserTypeAssignedFoundError: if a type assigned to user found
    """

    return BaseResponse(data=await service.delete_user_type(type_key=type_key))
