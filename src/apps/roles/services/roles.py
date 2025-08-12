"""Service with methods to set and get values."""

import copy
from collections import defaultdict
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, Path
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, delete, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.modules.models import ModulePermissionLink, Modules
from apps.modules.schemas import ModuleResponse
from apps.permissions.execeptions import InvalidModulePermissionError
from apps.roles.constants import RoleMessage, RolesSortBy
from apps.roles.execeptions import (
    RoleAlreadyExistsError,
    RoleAssignedFoundError,
    RoleNotFoundError,
)
from apps.roles.models import RoleModulePermissionLink, Roles
from apps.roles.schemas.response import BaseRoleResponse, RoleResponse
from apps.users.models.user import UserRoleLink
from core.db import db_session
from core.utils import logger
from core.utils.resolve_context_ids import get_context_ids_from_keys
from core.utils.schema import SuccessResponse
from core.utils.slug_utils import (
    generate_unique_slug,
    validate_and_generate_slug,
    validate_unique_slug,
)


class RoleService:
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
            tenant_id (int): tenant_id of tenant.
            app_id (int): app_id of tenant_app.
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

    async def _resolve_role_id(self, role_key: str | int) -> int:
        try:
            query = Roles.id == int(role_key)
        except (ValueError, TypeError):
            query = Roles.slug == role_key

        role_id = await self.session.scalar(
            select(Roles.id).where(
                and_(
                    query,
                    Roles.tenant_id == self.tenant_id,
                    Roles.app_id == self.app_id,
                    Roles.deleted_at.is_(None),
                )
            )
        )
        if not role_id:
            raise RoleNotFoundError

        return role_id

    async def _validate_module_permissions(
        self, module_permissions: list[dict[str, Any]]
    ) -> None:
        """Validate that the given module permissions exist and are valid."""
        for mp in module_permissions:
            module_id = mp["module_id"]
            permission_ids = mp["permission_ids"]

            # Verify all permissions exist for this module
            valid_permissions = await self.session.scalars(
                select(ModulePermissionLink.permission_id).where(
                    and_(
                        ModulePermissionLink.module_id == module_id,
                        ModulePermissionLink.permission_id.in_(permission_ids),
                    )
                )
            )
            valid_permission_ids = set(valid_permissions.all())
            if len(valid_permission_ids) != len(permission_ids):
                raise InvalidModulePermissionError

    async def _assign_module_permissions(
        self, role_id: int, module_permissions: list[dict[str, Any]]
    ) -> None:
        """Assign module permissions to a role."""
        # Delete existing assignments
        await self.session.execute(
            delete(RoleModulePermissionLink).where(
                RoleModulePermissionLink.role_id == role_id
            )
        )

        # Create new assignments
        for mp in module_permissions:
            module_id = mp["module_id"]
            if not mp["permission_ids"]:
                link = RoleModulePermissionLink(
                    role_id=role_id,
                    module_id=module_id,
                    permission_id=None,
                    tenant_id=self.tenant_id,
                    app_id=self.app_id,
                )
                self.session.add(link)
            else:
                for permission_id in mp["permission_ids"]:
                    link = RoleModulePermissionLink(
                        role_id=role_id,
                        module_id=module_id,
                        permission_id=permission_id,
                        tenant_id=self.tenant_id,
                        app_id=self.app_id,
                    )
                    self.session.add(link)

    async def create_role(
        self,
        name: str,
        slug: str,
        module_permissions: list[dict[str, Any]] | None = None,
        description: str | None = None,
        role_metadata: dict | None = None,
    ) -> Roles:
        """
        Create a new role.

        Args:
          - name (str): The name of the role (e.g., "Manager", "Editor").
          - module_permissions (list[ModulePermissionAssignment] | None):
                Optional list of module-permission assignments specifying what actions this role can perform.
          - slug (str | None): Optional slug for the role used for referencing or URL-friendly names.
          - description (str | None): Optional description of the role.
          - role_metadata (dict | None): Optional metadata for the role.

        Returns:
            Roles: RoleModel with newly created role.

        Raises:
            RoleAlreadyExistsError: If a role with the same name already exists.
        """

        await self._resolve_context_ids()

        async with self.session.begin_nested():
            if await self.session.scalar(
                select(Roles).where(
                    and_(
                        Roles.name.ilike(name),
                        Roles.tenant_id == self.tenant_id,
                        Roles.app_id == self.app_id,
                        Roles.deleted_at.is_(None),
                    )
                )
            ):
                raise RoleAlreadyExistsError

        slug = await validate_and_generate_slug(
            slug=slug,
            name=name,
            db=self.session,
            model=Roles,
            tenant_id=self.tenant_id,
            app_id=self.app_id,
        )

        async with self.session.begin_nested():
            role = Roles(
                name=name,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                slug=slug,
                description=description,
                role_metadata=role_metadata,
            )
            self.session.add(role)

        if module_permissions:
            async with self.session.begin_nested():
                await self._validate_module_permissions(module_permissions)
                await self._assign_module_permissions(role.id, module_permissions)

        async with self.session.begin_nested():
            await self.session.refresh(role)

        return role

    async def update_role(
        self,
        role_key: int | str,
        name: str | None,
        module_permissions: list[dict[str, Any]] | None,
        slug: str | None,
        description: str | None = None,
        role_metadata: dict | None = None,
    ) -> RoleResponse:
        """
        Update a role by its key.

        Args:
          - role_key (int | str): The unique identifier of the role (can be a numeric ID or a string slug).
          - name (str): Optional  The name of the role (e.g., "Manager", "Editor").
          - module_permissions (list[ModulePermissionAssignment] | None):
                Optional list of module-permission assignments specifying what actions this role can perform.
          - slug (str | None): Optional slug for the role used for referencing or URL-friendly names.
          - description (str | None): Optional description of the role.
          - role_metadata (dict | None): Optional metadata for the role.

        Returns:
            RoleResponse: The updated role details response.

        Raises:
            RoleNotFoundError: If the role with the given key is not found.
            RoleAlreadyExistsError: If a role with the same name already exists.

        """

        await self._resolve_context_ids()
        role_id = await self._resolve_role_id(role_key=role_key)

        async with self.session.begin_nested():
            role = await self.session.scalar(
                select(Roles).where(
                    and_(
                        Roles.id == role_id,
                        Roles.tenant_id == self.tenant_id,
                        Roles.app_id == self.app_id,
                        Roles.deleted_at.is_(None),
                    )
                )
            )
            if not role:
                raise RoleNotFoundError

        if name and name != role.name:
            async with self.session.begin_nested():
                # Check if new name conflicts with existing role
                if await self.session.scalar(
                    exists()
                    .where(
                        and_(
                            Roles.id != role_id,
                            Roles.name.ilike(name),
                            Roles.tenant_id == self.tenant_id,
                            Roles.app_id == self.app_id,
                            Roles.deleted_at.is_(None),
                        )
                    )
                    .select()
                ):
                    raise RoleAlreadyExistsError
            role.name = name

        if slug and role.slug != slug:
            await validate_unique_slug(
                slug,
                db=self.session,
                model=Roles,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
            )
            role.slug = slug
        elif role.name != name:
            role.slug = await generate_unique_slug(
                text=name,
                db=self.session,
                model=Roles,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                existing_id=role.id,
            )

        if module_permissions is not None:
            async with self.session.begin_nested():
                await self._validate_module_permissions(module_permissions)
                await self._assign_module_permissions(role_id, module_permissions)

        if description is not None:
            role.description = description

        if role_metadata is not None:
            role.role_metadata = role_metadata

        role.updated_at = datetime.now(UTC).replace(tzinfo=None)

        async with self.session.begin_nested():
            return await self.get_role_by_id(role_id)

    async def get_all_roles(
        self,
        page_params: Params,
        sortby: RolesSortBy | None = None,
        name: str | None = None,
    ) -> Page[BaseRoleResponse]:
        """
        Retrieve a paginated list of all roles with optional filtering and sorting.

        Args:
          - page_params (Params): Pagination parameters, including page number and size.
          - sortby (RolesSortBy | None): Optional sorting criteria (e.g., by name or created date).
          - name (str | None): Optional filter to return roles that match the given name or partial name.

        Returns:
          - Page[BaseRoleResponse]: A paginated response containing the list of roles.

        """
        await self._resolve_context_ids()

        query = select(Roles).where(
            and_(
                Roles.tenant_id == self.tenant_id,
                Roles.app_id == self.app_id,
                Roles.deleted_at.is_(None),
            )
        )

        if name:
            query = query.where(Roles.name.ilike(f"%{name.strip()}%"))

        sort_options = {
            RolesSortBy.NAME_ASC: Roles.name.asc(),
            RolesSortBy.NAME_DESC: Roles.name.desc(),
            None: Roles.created_at.desc(),
        }
        query = query.order_by(sort_options[sortby])

        return await paginate(self.session, query, page_params)

    async def get_role_by_id(self, role_key: int | str) -> RoleResponse:
        """
        Retrieve a role by its key.

        Args:
          - role_key (int | str): The unique identifier of the role (can be a numeric ID or a string slug).

        Returns:
            BaseResponse[RoleResponse]: The role's details wrapped in a base response format.

        Raises:
            RoleNotFoundError: If the role with the given key is not found.
        """

        await self._resolve_context_ids()
        role_id = await self._resolve_role_id(role_key=role_key)

        # Step 1: Fetch the Role entity itself
        role = await self.session.scalar(
            select(Roles).where(
                and_(
                    Roles.id == role_id,
                    Roles.tenant_id == self.tenant_id,
                    Roles.app_id == self.app_id,
                    Roles.deleted_at.is_(None),
                )
            )
        )
        if not role:
            raise RoleNotFoundError

        role_module_permission_links = await self.session.scalars(
            select(RoleModulePermissionLink).where(
                RoleModulePermissionLink.role_id == role_id
            )
        )
        role_module_permission_links = role_module_permission_links.unique().all()

        if not role_module_permission_links:
            return RoleResponse(
                id=role.id,
                name=role.name,
                slug=role.slug,
                description=role.description,
                role_metadata=role.role_metadata,
                modules=[],
            )

        module_ids = [link.module_id for link in role_module_permission_links]
        module_result = await self.session.scalars(
            select(Modules)
            .where(
                and_(
                    Modules.id.in_(module_ids),
                    Modules.deleted_at.is_(None),
                    Modules.tenant_id == self.tenant_id,
                    Modules.app_id == self.app_id,
                )
            )
            .options(
                selectinload(Modules.permissions), selectinload(Modules.child_modules)
            )
        )
        modules = list(module_result)
        if not modules:
            return RoleResponse(
                id=role.id,
                name=role.name,
                slug=role.slug,
                description=role.description,
                role_metadata=role.role_metadata,
                modules=[],
            )

        nested_modules = self.build_module_tree(
            modules, role_module_permission_links=role_module_permission_links
        )

        return RoleResponse(
            id=role.id,
            name=role.name,
            slug=role.slug,
            description=role.description,
            role_metadata=role.role_metadata,
            modules=nested_modules,
        )

    def build_module_tree(
        self,
        modules: list[Modules],
        role_module_permission_links: list[RoleModulePermissionLink],
    ) -> list[ModuleResponse]:
        filtered_modules = copy.deepcopy(modules)
        allowed_permissions = {
            (link.module_id, link.permission_id)
            for link in role_module_permission_links
        }

        id_to_module = {m.id: m for m in filtered_modules}

        for module in filtered_modules:
            module.child_modules = []
            module.permissions = [
                p
                for p in module.permissions
                if (module.id, p.id) in allowed_permissions
            ]

        roots = []
        for module in filtered_modules:
            if module.id not in {
                link.module_id for link in role_module_permission_links
            }:
                continue

            if module.parent_module_id:
                parent = id_to_module.get(module.parent_module_id)
                if parent:
                    parent.child_modules.append(module)
                else:
                    # Parent not found — treat as root
                    roots.append(module)
            else:
                # No parent — treat as root
                roots.append(module)

        return [ModuleResponse.model_validate(m, from_attributes=True) for m in roots]

    async def get_roles_by_ids(
        self, role_ids: list[int], tenant_id: int, app_id: int
    ) -> list[RoleResponse]:
        """Efficiently get a list of RoleResponse for
        the given list of role IDs using a single query."""

        if not role_ids:
            return []

        role_result = await self.session.scalars(
            select(Roles).where(
                and_(
                    Roles.id.in_(role_ids),
                    Roles.deleted_at.is_(None),
                    Roles.tenant_id == tenant_id,
                    Roles.app_id == app_id,
                )
            )
        )
        roles = list(role_result)

        if not roles:
            return []

        valid_role_ids = [role.id for role in roles]

        # Fetch role-module-permission links
        role_module_permission_links = await self.session.scalars(
            select(RoleModulePermissionLink).where(
                RoleModulePermissionLink.role_id.in_(valid_role_ids)
            )
        )
        role_module_permission_links = list(role_module_permission_links)

        role_response: list[RoleResponse] = []
        if not role_module_permission_links:
            return role_response.extend(
                RoleResponse(
                    id=role.id,
                    name=role.name,
                    slug=role.slug,
                    description=role.description,
                    role_metadata=role.role_metadata,
                    modules=[],
                )
                for role in roles
            )

        module_ids = [link.module_id for link in role_module_permission_links]
        module_result = await self.session.scalars(
            select(Modules)
            .where(
                and_(
                    Modules.id.in_(module_ids),
                    Modules.deleted_at.is_(None),
                    Modules.tenant_id == tenant_id,
                    Modules.app_id == app_id,
                )
            )
            .options(
                selectinload(Modules.permissions), selectinload(Modules.child_modules)
            )
        )
        modules = list(module_result)

        if not modules:
            return role_response.extend(
                RoleResponse(
                    id=role.id,
                    name=role.name,
                    slug=role.slug,
                    description=role.description,
                    role_metadata=role.role_metadata,
                    modules=[],
                )
                for role in roles
            )

        links_by_role = defaultdict(list)
        for link in role_module_permission_links:
            links_by_role[link.role_id].append(link)

        for role in roles:
            nested_modules = self.build_module_tree(
                modules, role_module_permission_links=links_by_role.get(role.id, [])
            )
            role_response.append(
                RoleResponse(
                    id=role.id,
                    name=role.name,
                    slug=role.slug,
                    description=role.description,
                    role_metadata=role.role_metadata,
                    modules=nested_modules,
                )
            )

        return role_response

    async def delete_role(self, role_key: int | str) -> SuccessResponse:
        """
        Delete a role by its key.

        Args:
            - role_key (int | str): The unique identifier of the role to be deleted (ID or slug).

        Returns:
            - SuccessResponse: A standardized success response indicating that the role was deleted.

        Raises:
            - RoleAssignedFoundError: If the role is assigned to any users.
        """

        await self._resolve_context_ids()
        role_id = await self._resolve_role_id(role_key=role_key)

        async with self.session.begin_nested():
            role = await self.session.scalar(
                select(Roles).where(
                    and_(
                        Roles.id == role_id,
                        Roles.tenant_id == self.tenant_id,
                        Roles.app_id == self.app_id,
                        Roles.deleted_at.is_(None),
                    )
                )
            )

            # Check if role is assigned to any users
            if await self.session.scalar(
                select(UserRoleLink).where(
                    and_(
                        UserRoleLink.role_id == role_id,
                        UserRoleLink.deleted_at.is_(None),
                    )
                )
            ):
                raise RoleAssignedFoundError

            # Soft delete role and its module permission links
            role.deleted_at = datetime.now(UTC).replace(tzinfo=None)
            await self.session.execute(
                update(RoleModulePermissionLink)
                .where(RoleModulePermissionLink.role_id == role_id)
                .values(deleted_at=datetime.now(UTC).replace(tzinfo=None))
            )

            logger.info(f"Role with ID {role_id} has been deleted.")

        return SuccessResponse(message=RoleMessage.ROLE_DELETED)
