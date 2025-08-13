"""Service with methods to set and get values of permissions."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
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
from core.utils.schema import SuccessResponse
from core.utils.slug_utils import (
    generate_unique_slug,
    validate_and_generate_slug,
    validate_unique_slug,
)
from apps.clients.models.clients import Clients


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
        self.client_slug = None
        self.client_id = None

    async def _resolve_context_ids(self) -> None:
        if self.client_id:
            return
        if not self.client_slug:
            raise ValueError("client_slug is required")
        
        # Get client ID from client slug
        from apps.clients.models.clients import Clients
        client = await self.session.scalar(
            select(Clients.id).where(
                and_(
                    Clients.slug == self.client_slug,
                    Clients.deleted_at.is_(None)
                )
            )
        )
        if not client:
            raise ValueError("Client not found")
        self.client_id = client.id

    async def _resolve_permission_id(self, permission_key: str | int) -> int:
        try:
            query = Permissions.id == int(permission_key)
        except (ValueError, TypeError):
            query = Permissions.slug == permission_key

        permission_id = await self.session.scalar(
            select(Permissions.id).where(
                and_(
                    query,
                    Permissions.client_id == self.client_id,
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
        client_id: str | None = None,
        user_id: str | None = None,
    ) -> Permissions:
        """Create a new permission.

        Args:
            name (str): The name of the permission.
            slug (str): The slug of the permission.
            description (str | None): Optional description of the permission.
            permission_metadata (dict | None): Optional metadata for the permission.
            client_id (str | None): Optional client ID.
            user_id (str | None): Optional user ID.
        Returns:
            Permissions: The newly created permission.

        Raises:
            PermissionAlreadyExistsError: If a permission with the same name already exists.
        """
        async with self.session.begin_nested():
            if await self.session.scalar(
                select(Permissions).where(
                    and_(
                        Permissions.name.ilike(name),
                        Permissions.client_id == client_id,
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
            client_id=client_id,
        )

        async with self.session.begin_nested():
            permission = Permissions(
                name=name,
                slug=slug,
                client_id=client_id,
                description=None,
                meta_data=None,
                created_by=user_id,
                updated_by=user_id,
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
        client_id: str | None = None,
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
        query = select(Permissions).where(Clients.id == client_id, Permissions.deleted_at.is_(None))

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

    async def update_permission(
        self,
        permission_key: int | str,
        name: str,
        slug: str | None = None,
        description: str | None = None,
        permission_metadata: dict | None = None,
        client_id: str | None = None,
        user_id: str | None = None,
    ) -> Permissions:
        """Update an existing permission.

        Args:
            permission_key (int | str): The permission ID or slug.
            name (str): The new name for the permission.
            slug (str | None): Optional new slug for the permission.
            description (str | None): Optional new description for the permission.
            permission_metadata (dict | None): Optional new metadata for the permission.
            client_id (str | None): Optional client ID.
            user_id (str | None): Optional user ID.
        Returns:
            Permissions: The updated permission object.

        Raises:
            PermissionNotFoundError: If the permission is not found.
            PermissionAlreadyExistsError: If a permission with the same name already exists.
        """
        permission_id = await self._resolve_permission_id(permission_key)

        async with self.session.begin_nested():
            permission = await self.session.get(Permissions, permission_id)
            if not permission:
                raise PermissionNotFoundError

            if name != permission.name:
                if await self.session.scalar(
                    select(Permissions).where(
                        and_(
                            Permissions.name.ilike(name),
                            Permissions.client_id == client_id,
                            Permissions.id != permission_id,
                            Permissions.deleted_at.is_(None),
                        )
                    )
                ):
                    raise PermissionAlreadyExistsError
                permission.name = name

            if slug and slug != permission.slug:
                await validate_unique_slug(
                    slug,
                    db=self.session,
                    model=Permissions,
                    client_id=client_id,
                )
                permission.slug = slug
            elif name != permission.name:
                permission.slug = await generate_unique_slug(
                    text=name,
                    db=self.session,
                    model=Permissions,
                    client_id=client_id,
                    existing_id=permission_id,
                )

            if description is not None:
                permission.description = description

            if permission_metadata is not None:
                permission.meta_data = permission_metadata

            permission.updated_by = user_id
            permission.updated_at = datetime.now(UTC).replace(tzinfo=None)

        async with self.session.begin_nested():
            await self.session.refresh(permission)

        return permission

    async def delete_permission(self, permission_key: int | str, client_id: str | None = None, user_id: str | None = None) -> SuccessResponse:
        """Delete a permission by its ID or slug.

        Args:
            permission_key (int | str): The permission ID or slug.
            client_id (str | None): Optional client ID.
            user_id (str | None): Optional user ID.
        Returns:
            SuccessResponse: Success message.

        Raises:
            PermissionNotFoundError: If the permission is not found.
            PermissionAssignedFoundError: If the permission is assigned to a role.
        """ 
        permission_id = await self._resolve_permission_id(permission_key)

        # Check if permission is assigned to any role
        if await self.session.scalar(
            select(RoleModulePermissionLink).where(
                RoleModulePermissionLink.permission_id == permission_id
            )
        ):
            raise PermissionAssignedFoundError

        async with self.session.begin_nested():
            permission = await self.session.get(Permissions, permission_id)
            if not permission:
                raise PermissionNotFoundError

            permission.deleted_at = datetime.now(UTC).replace(tzinfo=None)
            permission.deleted_by = user_id
        return SuccessResponse(message=PermissionMessage.PERMISSION_DELETED)
