"""routes for permission operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_pagination import Page, Params

from apps.permissions.constants import PermissionSortBy
from apps.permissions.schemas.response import BasePermissionResponse
from apps.permissions.services.permissions import PermissionService
from apps.users.models.user import Users
from apps.users.utils import current_user
from core.constants import SortType
from core.utils.schema import BaseResponse

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


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
            params=params, sort_by=sort_by, sort_type=sort_type, search=search
        )
    )
