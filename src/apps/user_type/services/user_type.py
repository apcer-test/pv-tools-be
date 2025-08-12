from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Path
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from apps.user_types.constants import UserTypeMessage, UserTypeSortBy
from apps.user_types.execeptions import (
    UserTypeAlreadyExistsError,
    UserTypeAssignedFoundError,
    UserTypeNotFoundError,
)
from apps.user_types.models import UserTypes
from apps.user_types.schemas.response import BaseUserTypeResponse
from apps.users.models import Users
from core.constants import SortType
from core.db import db_session
from core.utils.resolve_context_ids import get_context_ids_from_keys
from core.utils.schema import SuccessResponse
from core.utils.slug_utils import (
    generate_unique_slug,
    validate_and_generate_slug,
    validate_unique_slug,
)


class UserTypeService:
    """Service with methods to set and get values."""

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        tenant_key: Annotated[int | str, Path()],
        app_key: Annotated[int | str, Path()],
    ) -> None:
        """Call method to inject db_session as a dependency.

        This method also calls a database connection which is injected here.

        Args:
            session (AsyncSession): An asynchronous database connection.
        """
        self.session = session
        self.tenant_key = tenant_key
        self.app_key = app_key
        self.tenant_id = None
        self.app_id = None

    async def _resolve_context_ids(self) -> None:
        if self.tenant_id and self.app_id:
            return
        tenant_id, app_id = await get_context_ids_from_keys(
            session=self.session, tenant_key=self.tenant_key, app_key=self.app_key
        )
        self.tenant_id = tenant_id
        self.app_id = app_id

    async def _resolve_type_id(self, type_key: str | int) -> int:
        try:
            query = UserTypes.id == int(type_key)
        except (ValueError, TypeError):
            query = UserTypes.slug == type_key

        type_id = await self.session.scalar(
            select(UserTypes.id).where(
                and_(
                    query,
                    UserTypes.tenant_id == self.tenant_id,
                    UserTypes.app_id == self.app_id,
                    UserTypes.deleted_at.is_(None),
                )
            )
        )
        if not type_id:
            raise UserTypeNotFoundError

        return type_id

    async def create_user_type(
        self,
        name: str,
        slug: str | None,
        description: str | None = None,
        user_type_metadata: dict | None = None,
    ) -> UserTypes:
        """
        Create a new user type.

        Args:
          - name (str): The name of the user type.
          - slug (str | None): Optional slug for the user type used for referencing or URL-friendly names.
          - description (str | None): Optional description of the user type.
          - user_type_metadata (dict | None): Optional metadata for the user type.

        Returns:
          - UserTypes: UserTypeModel of newly created user type.

        Raises:
          - UserTypeAlreadyExistsError: If a user type with the same name already exists.
        """
        await self._resolve_context_ids()

        # Check if the user's type already exists
        async with self.session.begin_nested():
            user_type = await self.session.scalar(
                select(UserTypes)
                .options(load_only(UserTypes.name))
                .where(
                    UserTypes.tenant_id == self.tenant_id,
                    UserTypes.app_id == self.app_id,
                    UserTypes.name.ilike(name),
                    UserTypes.deleted_at.is_(None),
                )
            )
        if user_type:
            raise UserTypeAlreadyExistsError

        slug = await validate_and_generate_slug(
            slug=slug,
            name=name,
            db=self.session,
            model=UserTypes,
            tenant_id=self.tenant_id,
            app_id=self.app_id,
        )

        async with self.session.begin_nested():
            user_type = UserTypes(
                name=name,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                slug=slug,
                description=description,
                user_type_metadata=user_type_metadata,
            )
            self.session.add(user_type)

        async with self.session.begin_nested():
            await self.session.refresh(user_type)

        return user_type

    async def get_all_user_types(
        self,
        page_params: Params,
        sort_by: UserTypeSortBy | None,
        sort_type: SortType | None,
        search: str | None,
    ) -> Page[UserTypes]:
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
        await self._resolve_context_ids()

        query = (
            select(UserTypes)
            .options(
                load_only(
                    UserTypes.id,
                    UserTypes.name,
                    UserTypes.slug,
                    UserTypes.description,
                    UserTypes.user_type_metadata,
                )
            )
            .where(
                UserTypes.tenant_id == self.tenant_id,
                UserTypes.app_id == self.app_id,
                UserTypes.deleted_at.is_(None),
            )
        )

        if search:
            query = query.where(UserTypes.name.ilike(f"%{search}%"))

        if sort_by:
            if sort_by == UserTypeSortBy.NAME:
                query = query.order_by(
                    UserTypes.name.asc()
                    if sort_type == SortType.ASC
                    else UserTypes.name.desc()
                )
            if sort_by == UserTypeSortBy.CREATED_AT:
                query = query.order_by(
                    UserTypes.created_at.asc()
                    if sort_type == SortType.ASC
                    else UserTypes.created_at.desc()
                )

        return await paginate(self.session, query, page_params)

    async def get_user_type_by_id(self, type_key: int | str) -> BaseUserTypeResponse:
        """
        Retrieve a specific user type by its ID or key.

        Args:
          type_key (int|str): The ID of the user type to retrieve.

        Returns:
          UserTypes : UserTypeModel for a specific type_key.

        Raises:
          UserTypeNotFoundError: If a type with the specified id not found.

        """
        await self._resolve_context_ids()
        type_id = await self._resolve_type_id(type_key=type_key)

        user_type = await self.session.scalar(
            select(UserTypes)
            .options(
                load_only(
                    UserTypes.id,
                    UserTypes.name,
                    UserTypes.slug,
                    UserTypes.description,
                    UserTypes.user_type_metadata,
                )
            )
            .where(
                UserTypes.tenant_id == self.tenant_id,
                UserTypes.app_id == self.app_id,
                UserTypes.id == type_id,
                UserTypes.deleted_at.is_(None),
            )
        )
        if not user_type:
            raise UserTypeNotFoundError

        return user_type

    async def delete_user_type(self, type_key: int | str) -> SuccessResponse:
        """
        Delete a user type by its ID or key.

        Args:
          - type_key (int | str): The unique identifier (ID or key) of the user type to delete.

        Returns:
          - BaseResponse[SuccessResponse]: A success message confirming deletion.

        Raises:
          - UserTypeNotFoundError: If a type with the specified id not found.
          - UserTypeAssignedFoundError: if a type assigned to user found
        """
        await self._resolve_context_ids()
        type_id = await self._resolve_type_id(type_key=type_key)

        user_type = await self.session.scalar(
            select(UserTypes)
            .options(load_only(UserTypes.id, UserTypes.name))
            .where(
                UserTypes.tenant_id == self.tenant_id,
                UserTypes.app_id == self.app_id,
                UserTypes.id == type_id,
                UserTypes.deleted_at.is_(None),
            )
        )
        if not user_type:
            raise UserTypeNotFoundError

        users_with_user_type = await self.session.scalars(
            select(Users)
            .options(load_only(Users.id))
            .where(
                Users.tenant_id == self.tenant_id,
                Users.app_id == self.app_id,
                Users.type_id == type_id,
                Users.deleted_at.is_(None),
            )
        )
        users_with_user_type = users_with_user_type.all()
        if users_with_user_type:
            raise UserTypeAssignedFoundError

        user_type.deleted_at = datetime.now(UTC).replace(tzinfo=None)

        return SuccessResponse(message=UserTypeMessage.USERTYPE_DELETED)

    async def update_user_type(
        self,
        type_key: int | str,
        name: str,
        slug: str | None,
        description: str | None = None,
        user_type_metadata: dict | None = None,
    ) -> UserTypes:
        """
        Update an existing user type.

        Args:
          - type_key (int | str): The unique identifier (ID or key) of the user type to update.
          - name (str): The updated name of the user type.
          - slug (str | None): Optional slug for the user type used for referencing or URL-friendly names.
          - description (str | None): Optional description of the user type.
          - user_type_metadata (dict | None): Optional metadata for the user type.

        Returns:
            BaseResponse[BaseUserTypeResponse]: A response containing the updated user type data.

        Raises:
            UserTypeNotFoundError: If a type with the specified id not found.
        """
        await self._resolve_context_ids()
        type_id = await self._resolve_type_id(type_key=type_key)

        existing_user_type = await self.session.scalar(
            select(UserTypes)
            .options(load_only(UserTypes.id, UserTypes.name, UserTypes.slug))
            .where(and_(UserTypes.id == type_id, UserTypes.deleted_at.is_(None)))
        )
        if not existing_user_type:
            raise UserTypeNotFoundError

        if name and name != existing_user_type.name:
            async with self.session.begin_nested():
                if await self.session.scalar(
                    select(UserTypes).where(
                        and_(
                            UserTypes.id != type_id,
                            UserTypes.name.ilike(name),
                            UserTypes.tenant_id == self.tenant_id,
                            UserTypes.app_id == self.app_id,
                            UserTypes.deleted_at.is_(None),
                        )
                    )
                ):
                    raise UserTypeAlreadyExistsError

        if slug and existing_user_type.slug != slug:
            await validate_unique_slug(
                slug,
                db=self.session,
                model=UserTypes,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
            )
            existing_user_type.slug = slug
        elif existing_user_type.name != name:
            existing_user_type.slug = await generate_unique_slug(
                text=name,
                db=self.session,
                model=UserTypes,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                existing_id=existing_user_type.id,
            )
        existing_user_type.name = name

        if description is not None:
            existing_user_type.description = description

        if user_type_metadata is not None:
            existing_user_type.user_type_metadata = user_type_metadata

        self.session.add(existing_user_type)
        await self.session.commit()
        return existing_user_type
