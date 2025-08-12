"""Service with methods to set and get values of permissions."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Path
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from apps.permissions.constants import PermissionMessage, PermissionSortBy
from apps.permissions.execeptions import (
    PermissionAlreadyExistsError,
    PermissionAssignedFoundError,
    PermissionNotFoundError,
)
from apps.permissions.models import Permissions
from apps.permissions.schemas.response import BasePermissionResponse
from apps.roles.models import RoleModulePermissionLink
from core.constants import SortType
from core.db import db_session
from core.utils.resolve_context_ids import get_context_ids_from_keys
from core.utils.schema import SuccessResponse
from core.utils.slug_utils import (
    generate_unique_slug,
    validate_and_generate_slug,
    validate_unique_slug,
)


class PermissionService:
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
            tenant_id (int): The tenant ID.
            app_id (int): The app ID.
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

    async def _resolve_permission_id(self, permission_key: str | int) -> int:
        try:
            query = Permissions.id == int(permission_key)
        except (ValueError, TypeError):
            query = Permissions.slug == permission_key

        permission_id = await self.session.scalar(
            select(Permissions.id).where(
                and_(
                    query,
                    Permissions.tenant_id == self.tenant_id,
                    Permissions.app_id == self.app_id,
                    Permissions.deleted_at.is_(None),
                )
            )
        )
        if not permission_id:
            raise PermissionNotFoundError

        return permission_id

    async def create_permission(
        self,
        name: str,
        slug: str,
        description: str | None = None,
        permission_metadata: dict | None = None,
    ) -> Permissions:
        """
        Create a new permission.

        Args:
            - name (str): The name of the permission. This is required.
            - slug (str): The slug of the permission. This is optional.
            - description (str | None): Optional description of the permission.
            - permission_metadata (dict | None): Optional metadata for the permission.

        Returns:
            Permissions: The Permission Model with the created permission.

        Raises:
            PermissionAlreadyExistsError: If a permission with the same name already exists.
        """
        await self._resolve_context_ids()

        async with self.session.begin_nested():
            if await self.session.scalar(
                select(Permissions)
                .options(load_only(Permissions.name))
                .where(
                    and_(
                        Permissions.tenant_id == self.tenant_id,
                        Permissions.app_id == self.app_id,
                        Permissions.name.ilike(name),
                        Permissions.deleted_at.is_(None),
                    )
                )
            ):
                raise PermissionAlreadyExistsError

        slug = await validate_and_generate_slug(
            slug=slug,
            name=name,
            db=self.session,
            model=Permissions,
            tenant_id=self.tenant_id,
            app_id=self.app_id,
        )

        async with self.session.begin_nested():
            permission = Permissions(
                name=name,
                slug=slug,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                description=description,
                permission_metadata=permission_metadata,
            )
            self.session.add(permission)

        async with self.session.begin_nested():
            await self.session.refresh(permission)

        return permission

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

        await self._resolve_context_ids()

        query = select(Permissions).where(
            Permissions.tenant_id == self.tenant_id,
            Permissions.app_id == self.app_id,
            Permissions.deleted_at.is_(None),
        )

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

    async def get_permission_by_id(self, permission_key: int | str) -> Permissions:
        """
        Retrieve a permission by its unique permission_key(ID/Name).

        Args:
          - permission_key (int | str): The unique identifier (ID/Name) of the permission.

        Returns:
          - Permissions: The Permission Model with the specified permission_key.

        Raises:
          - PermissionNotFoundError: If no permission is found with the given key.
        """

        await self._resolve_context_ids()
        permission_id = await self._resolve_permission_id(permission_key=permission_key)

        permission = await self.session.scalar(
            select(Permissions).where(
                Permissions.id == permission_id,
                Permissions.tenant_id == self.tenant_id,
                Permissions.app_id == self.app_id,
                Permissions.deleted_at.is_(None),
            )
        )

        if not permission:
            raise PermissionNotFoundError

        return permission

    async def delete_permission(self, permission_key: int | str) -> SuccessResponse:
        """
        Delete a permission by its unique permission_key.

        Args:
          - permission_key (int | str): The unique identifier (ID or key) of the permission to delete.

        Returns:
          - SuccessResponse: A success message upon successful deletion.

        Raises:
          - PermissionNotFoundError: If no permission is found with the given key.
          - PermissionAssignedFoundError: If a permission assigned to user found.
        """
        await self._resolve_context_ids()
        permission_id = await self._resolve_permission_id(permission_key=permission_key)

        existing_permission = await self.session.scalar(
            select(Permissions)
            .options(load_only(Permissions.id, Permissions.name))
            .where(
                and_(
                    Permissions.tenant_id == self.tenant_id,
                    Permissions.app_id == self.app_id,
                    Permissions.id == permission_id,
                    Permissions.deleted_at.is_(None),
                )
            )
        )
        if not existing_permission:
            raise PermissionNotFoundError

        all_users_with_permission = await self.session.scalars(
            select(RoleModulePermissionLink)
            .options(load_only(RoleModulePermissionLink.id))
            .where(
                and_(
                    RoleModulePermissionLink.permission_id == permission_id,
                    RoleModulePermissionLink.deleted_at.is_(None),
                )
            )
        )
        user_list_with_permission = [per.id for per in all_users_with_permission]
        if user_list_with_permission:
            raise PermissionAssignedFoundError

        existing_permission.deleted_at = datetime.now(UTC).replace(tzinfo=None)

        return SuccessResponse(message=PermissionMessage.PERMISSION_DELETED)

    async def update_permission(
        self,
        permission_key: int | str,
        name: str,
        slug: str,
        description: str | None = None,
        permission_metadata: dict | None = None,
    ) -> Permissions:
        """
        Update an existing permission.

        Args:
          - permission_key (int | str): The unique identifier (ID or key) of the permission to update.
          - name (str): The name of the permission. This is required.
          - slug (str): The slug of the permission. This is optional.
          - description (str | None): Optional description of the permission.
          - permission_metadata (dict | None): Optional metadata for the permission.

        Returns:
          - Permissions: Permission Model with updated details

        Raises:
          - PermissionNotFoundError: If no permission is found with the given key.
        """

        await self._resolve_context_ids()
        permission_id = await self._resolve_permission_id(permission_key=permission_key)

        existing_permission = await self.session.scalar(
            select(Permissions)
            .options(
                load_only(
                    Permissions.id,
                    Permissions.name,
                    Permissions.slug,
                    Permissions.description,
                    Permissions.permission_metadata,
                )
            )
            .where(
                and_(
                    Permissions.tenant_id == self.tenant_id,
                    Permissions.app_id == self.app_id,
                    Permissions.id == permission_id,
                    Permissions.deleted_at.is_(None),
                )
            )
        )
        if not existing_permission:
            raise PermissionNotFoundError

        if name and name != existing_permission.name:
            async with self.session.begin_nested():
                if await self.session.scalar(
                    select(Permissions).where(
                        and_(
                            Permissions.id != permission_id,
                            Permissions.name.ilike(name),
                            Permissions.tenant_id == self.tenant_id,
                            Permissions.app_id == self.app_id,
                            Permissions.deleted_at.is_(None),
                        )
                    )
                ):
                    raise PermissionAlreadyExistsError

        if slug and existing_permission.slug != slug:
            await validate_unique_slug(
                slug,
                db=self.session,
                model=Permissions,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
            )
            existing_permission.slug = slug
        elif existing_permission.name != name:
            existing_permission.slug = await generate_unique_slug(
                text=name,
                db=self.session,
                model=Permissions,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                existing_id=existing_permission.id,
            )

        existing_permission.name = name

        if description is not None:
            existing_permission.description = description

        if permission_metadata is not None:
            existing_permission.permission_metadata = permission_metadata

        existing_permission.updated_at = datetime.now(UTC).replace(tzinfo=None)

        return existing_permission
