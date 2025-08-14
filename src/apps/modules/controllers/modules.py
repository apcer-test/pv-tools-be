from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_pagination import Page, Params

from apps.modules.constants import ModuleSortBy
from apps.modules.schemas import ModuleResponse
from apps.modules.services import ModuleService
from apps.users.models.user import Users
from apps.users.utils import current_user
from core.constants import SortType
from core.utils.schema import BaseResponse

router = APIRouter(
    prefix="/modules", tags=["Modules"],
)


@router.get(
    "", status_code=status.HTTP_200_OK, name="List Modules", operation_id="list_modules"
)
async def get_all_modules(
    service: Annotated[ModuleService, Depends()],
    params: Annotated[Params, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
    sort_by: Annotated[ModuleSortBy | None, Query()] = None,
    sort_type: Annotated[SortType | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> BaseResponse[Page[ModuleResponse]]:
    """
    Retrieve a paginated list of modules.

    Args:

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