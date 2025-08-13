from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from apps.user_type.constants import UserTypeSortBy
from apps.user_type.models import UserType
from apps.clients.models.clients import Clients
from core.constants import SortType
from core.db import db_session


class UserTypeService:
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

    async def get_all_user_types(
        self,
        page_params: Params,
        sort_by: UserTypeSortBy | None,
        sort_type: SortType | None,
        search: str | None,
        client_id: str,
    ) -> Page[UserType]:
        """
        Retrieve a paginated list of user types with optional sorting and searching.

        Args:
          - page_params (Params): Pagination parameters like page number and size.
          - sort_by (UserTypeSortBy | None): Field by which to sort the results.
          - sort_type (SortType | None): Sort order, either ascending or descending.
          - search (str | None): Keyword to filter user types by name or description.

        Returns:
          -  Page[UserTypes]: A paginated response containing the list of user types.
        """

        query = (
            select(UserType)
            .join(Clients, UserType.client_id == Clients.id)
            .options(
                load_only(
                    UserType.id,
                    UserType.name,
                    UserType.slug,
                    UserType.description,
                    UserType.meta_data,
                )
            )
            .where(
                Clients.id == client_id,
                UserType.deleted_at.is_(None),
            )
        )

        if search:
            query = query.where(UserType.name.ilike(f"%{search}%"))

        if sort_by:
            if sort_by == UserTypeSortBy.NAME:
                query = query.order_by(
                    UserType.name.asc()
                    if sort_type == SortType.ASC
                    else UserType.name.desc()
                )
            if sort_by == UserTypeSortBy.CREATED_AT:
                query = query.order_by(
                    UserType.created_at.asc()
                    if sort_type == SortType.ASC
                    else UserType.created_at.desc()
                )

        return await paginate(self.session, query, page_params)
