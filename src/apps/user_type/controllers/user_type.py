from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.params import Query
from fastapi_pagination import Page, Params

from apps.user_type.constants import UserTypeSortBy
from apps.user_type.schemas.response import BaseUserTypeResponse
from apps.user_type.services.user_type import UserTypeService
from apps.users.models.user import Users
from apps.users.utils import current_user
from core.constants import SortType
from core.utils.schema import BaseResponse

router = APIRouter(
    prefix="/user-types",
    tags=["User Types"],
)

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    name="Get all user types",
    operation_id="get-all-user-types",
)
async def get_all_user_types(
    service: Annotated[UserTypeService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
    page_params: Annotated[Params, Depends()],
    sort_by: Annotated[UserTypeSortBy | None, Query()] = None,
    sort_type: Annotated[SortType | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> BaseResponse[Page[BaseUserTypeResponse]]:
    """
    Retrieve a paginated list of user types with optional sorting and searching.

    Args:
      - page_params (Params): Pagination parameters like page number and size.
      - sort_by (UserTypeSortBy | None): Field by which to sort the results.
      - sort_type (SortType | None): Sort order, either ascending or descending.
      - search (str | None): Keyword to filter user types by name or description.

    Returns:
      - BaseResponse[Page[BaseUserTypeResponse]]: A paginated response containing the list of user types wrapped in a BaseResponse.
    """

    return BaseResponse(
        data=await service.get_all_user_types(
            page_params=page_params, sort_by=sort_by, sort_type=sort_type, search=search, client_id=user.get("client_id")
        )
    )
