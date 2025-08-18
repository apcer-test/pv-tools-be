"""Service with methods to set and get values of permissions."""

from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.permissions.constants import PermissionSortBy
from apps.permissions.execeptions import PermissionNotFoundError
from apps.permissions.models import Permissions
from apps.permissions.schemas.response import BasePermissionResponse
from core.constants import SortType
from core.db import db_session


class PermissionService:
    """Service with methods to set and get values."""

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
    ) -> None:
        """Call method to inject db_session as a dependency.

        This method also calls a database connection which is injected here.

        Args:
            session (AsyncSession): An asynchronous database connection.
        """
        self.session = session

    async def get_all_permissions(
        self,
        params: Params,
        sort_by: PermissionSortBy | None = None,
        sort_type: SortType | None = None,
        search: str | None = None,
    ) -> Page[BasePermissionResponse]:
        """
        Retrieve a paginated list of all permissions.

        Args:
            - params (Params): Pagination parameters including page number and size.
            - sort_by (PermissionSortBy | None): Field to sort the results by. Optional.
            - sort_type (SortType | None): Sorting order (asc or desc). Optional.
            - search (str | None): Search term to filter permissions by name. Optional.

        Returns:
            - Page[BasePermissionResponse]: A paginated list of permissions.

        Raises:
            - PermissionNotFoundError: If a permission with the same name not exists.
        """
        query = select(Permissions).where(Permissions.deleted_at.is_(None))

        if search:
            query = query.where(Permissions.name.ilike(f"%{search.strip()}%"))

        if sort_by:
            if sort_by == PermissionSortBy.NAME:
                query = query.order_by(
                    Permissions.name.asc()
                    if sort_type == SortType.ASC
                    else Permissions.name.desc()
                )
            elif sort_by == PermissionSortBy.CREATED_AT:
                query = query.order_by(
                    Permissions.created_at.asc()
                    if sort_type == SortType.ASC
                    else Permissions.created_at.desc()
                )

        result = await paginate(self.session, query, params)
        if not result.items:
            raise PermissionNotFoundError

        return result
