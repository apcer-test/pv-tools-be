"""Service with methods to set and get values."""

import copy
from collections import defaultdict
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends
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
from apps.roles.schemas.response import BaseRoleResponse, RoleResponse, ModuleBasicResponse, RoleStatusResponse
from apps.users.models.user import UserRoleLink
from core.db import db_session
from core.utils import logger
from core.utils.schema import SuccessResponse
from core.utils.slug_utils import (
    generate_unique_slug,
    validate_and_generate_slug,
    validate_unique_slug,
)
from apps.clients.models.clients import Clients


class RoleService:
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
        self, role_id: str, module_permissions: list[dict[str, Any]], client_id: str | None = None
    ) -> None:
        """Assign module permissions to a role."""
        for mp in module_permissions:
            module_id = mp["module_id"]
            permission_ids = mp["permission_ids"]

            for permission_id in permission_ids:
                link = RoleModulePermissionLink(
                    role_id=role_id,
                    module_id=module_id,
                    permission_id=permission_id,
                    client_id=client_id,
                )
                self.session.add(link)

    async def create_role(
        self,
        name: str,
        module_permissions: list[dict[str, Any]] | None = None,
        description: str | None = None,
        role_metadata: dict | None = None,
        client_id: str | None = None,
        user_id: str | None = None,
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
          - client_id (str | None): Optional client ID.
          - user_id (str | None): Optional user ID.
        Returns:
            Roles: RoleModel with newly created role.

        Raises:
            RoleAlreadyExistsError: If a role with the same name already exists.
        """

        async with self.session.begin_nested():
            if await self.session.scalar(
                select(Roles).where(
                    and_(
                        Roles.name.ilike(name),
                        Roles.client_id == client_id,
                        Roles.deleted_at.is_(None),
                    )
                )
            ):
                raise RoleAlreadyExistsError

        slug = await validate_and_generate_slug(
            name=name,
            db=self.session,
            model=Roles,
            client_id=client_id,
            slug=None,
        )

        async with self.session.begin_nested():
            role = Roles(
                name=name,
                client_id=client_id,
                slug=slug,
                description=description,
                meta_data=role_metadata,
                created_by=user_id,
                updated_by=user_id,
            )
            self.session.add(role)

        if module_permissions:
            async with self.session.begin_nested():
                await self._validate_module_permissions(module_permissions)
                await self._assign_module_permissions(role.id, module_permissions, client_id)

        async with self.session.begin_nested():
            await self.session.refresh(role)

        return role

    async def update_role(
        self,
        role_id: str,
        name: str | None,
        module_permissions: list[dict[str, Any]] | None,
        description: str | None = None,
        reason: str | None = None,
        role_metadata: dict | None = None,
        client_id: str | None = None,
        user_id: str | None = None,
    ) -> RoleResponse:
        """
        Update a role by its key.

        Args:
        - role_id (str): The unique identifier of the role (can be a numeric ID or a string slug).
        - name (str): Optional  The name of the role (e.g., "Manager", "Editor").
        - module_permissions (list[ModulePermissionAssignment] | None):
                Optional list of module-permission assignments specifying what actions this role can perform.
        - description (str | None): Optional description of the role.
        - role_metadata (dict | None): Optional metadata for the role.
        - client_id (str | None): Optional client ID.
        - user_id (str | None): Optional user ID.
        Returns:
            RoleResponse: The updated role details response.

        Raises:
            RoleNotFoundError: If the role with the given key is not found.
            RoleAlreadyExistsError: If a role with the same name already exists.
        """
        
        # Step 1: Retrieve the role
        async with self.session.begin_nested():
            role = await self.session.scalar(
                select(Roles).where(
                    and_(
                        Roles.id == role_id,
                        Roles.client_id == client_id,
                        Roles.deleted_at.is_(None),
                    )
                )
            )
            if not role:
                raise RoleNotFoundError

        # Step 2: Check and update the role name if necessary
        if name and name != role.name:
            async with self.session.begin_nested():
                # Check if new name conflicts with existing role
                if await self.session.scalar(
                    exists()
                    .where(
                        and_(
                            Roles.id != role_id,
                            Roles.name.ilike(name),
                            Roles.client_id == client_id,
                            Roles.deleted_at.is_(None),
                        )
                    )
                    .select()
                ):
                    raise RoleAlreadyExistsError
            role.name = name

        # Step 3: Update the description if provided
        if description is not None:
            role.description = description

        # Step 4: Update metadata if provided
        if role_metadata is not None:
            role.meta_data = role_metadata

        # Step 5: Remove old module permissions and assign new ones if provided
        if module_permissions is not None:
            async with self.session.begin_nested():
                # Remove old module permissions for the role
                await self.session.execute(
                    delete(RoleModulePermissionLink).where(
                        and_(
                            RoleModulePermissionLink.role_id == role_id,
                            RoleModulePermissionLink.client_id == client_id,
                        )
                    )
                )

                # Validate and assign new module permissions
                await self._validate_module_permissions(module_permissions)
                await self._assign_module_permissions(role_id, module_permissions, client_id)

        # Step 6: Set the updated_by field and updated_at field
        role.updated_by = user_id
        role.updated_at = datetime.now(UTC).replace(tzinfo=None)

        # Step 7: Commit changes and return the updated role
        async with self.session.begin_nested():
            return await self.get_role_by_id(role_id=role_id, client_id=client_id)

    async def get_all_roles(
        self,
        page_params: Params,
        sortby: RolesSortBy | None = None,
        name: str | None = None,
        client_id: str | None = None,
    ) -> Page[BaseRoleResponse]:
        """
        Retrieve a paginated list of all roles with optional filtering and sorting.

        Args:
          - page_params (Params): Pagination parameters, including page number and size.
          - sortby (RolesSortBy | None): Optional sorting criteria (e.g., by name or created date).
          - name (str | None): Optional filter to return roles that match the given name or partial name.
          - client_id (str | None): Optional client ID.
        Returns:
          - Page[BaseRoleResponse]: A paginated response containing the list of roles.

        """

        query = select(Roles).where(
            Clients.id == client_id,
            Roles.deleted_at.is_(None),
        )

        if name:
            query = query.where(Roles.name.ilike(f"%{name.strip()}%"))

        sort_options = {
            RolesSortBy.NAME_ASC: Roles.name.asc(),
            RolesSortBy.NAME_DESC: Roles.name.desc(),
            None: Roles.created_at.desc(),
        }
        query = query.order_by(sort_options[sortby])

        result = await paginate(self.session, query, page_params)        
        return result

    async def get_role_by_id(self, role_id: str, client_id: str | None = None) -> RoleResponse:
        """
        Retrieve a role by its key.

        Args:
          - role_id (str): The unique identifier of the role (can be a numeric ID or a string slug).
          - client_id (str | None): Optional client ID.
        Returns:
            BaseResponse[RoleResponse]: The role's details wrapped in a base response format.

        Raises:
            RoleNotFoundError: If the role with the given key is not found.
        """

        # Step 1: Fetch the Role entity itself
        role = await self.session.scalar(
            select(Roles).where(
                and_(
                    Roles.id == role_id,
                    Roles.client_id == client_id,
                    Roles.deleted_at.is_(None),
                )
            )
        )
        if not role:
            raise RoleNotFoundError

        role_module_permission_links = await self.session.scalars(
            select(RoleModulePermissionLink).where(
                and_(
                    RoleModulePermissionLink.role_id == role_id,
                    RoleModulePermissionLink.client_id == client_id,
                )
            )
        )
        role_module_permission_links = role_module_permission_links.unique().all()

        if not role_module_permission_links:
            return RoleResponse(
                id=role_id,
                name=role.name,
                slug=role.slug,
                description=role.description,
                role_metadata=role.meta_data,
                modules=[],
            )

        # Get all module IDs that have permissions for this role
        direct_module_ids = [link.module_id for link in role_module_permission_links]
        
        # First, fetch all modules that have direct permission links
        direct_modules_result = await self.session.scalars(
            select(Modules)
            .where(Modules.id.in_(direct_module_ids), Modules.deleted_at.is_(None))
            .options(selectinload(Modules.permissions), selectinload(Modules.child_modules))
        )
        direct_modules = list(direct_modules_result)
        
        # Get all parent module IDs from the direct modules
        parent_module_ids = set()
        for module in direct_modules:
            if module.parent_module_id:
                parent_module_ids.add(module.parent_module_id)
        
        # Fetch parent modules if they exist
        parent_modules = []
        if parent_module_ids:
            parent_modules_result = await self.session.scalars(
                select(Modules)
                .where(Modules.id.in_(parent_module_ids), Modules.deleted_at.is_(None))
                .options(selectinload(Modules.permissions), selectinload(Modules.child_modules))
            )
            parent_modules = list(parent_modules_result)
        
        # Combine all modules (direct + parent)
        all_modules = direct_modules + parent_modules
        
        if not all_modules:
            return RoleResponse(
                id=role_id,
                name=role.name,
                slug=role.slug,
                description=role.description,
                role_metadata=role.meta_data,
                modules=[],
            )

        nested_modules = self.build_module_tree(
            all_modules, role_module_permission_links=role_module_permission_links
        )

        return RoleResponse(
            id=role_id,
            name=role.name,
            slug=role.slug,
            description=role.description,
            role_metadata=role.meta_data,
            modules=nested_modules,
        )

    def build_module_tree(
        self,
        modules: list[Modules],
        role_module_permission_links: list[RoleModulePermissionLink],
    ) -> list[ModuleBasicResponse]:
        """
        Builds a hierarchical tree structure for modules, ensuring parent modules
        are included even if only child modules have permissions.
        """
        filtered_modules = copy.deepcopy(modules)
        allowed_permissions = {
            (link.module_id, link.permission_id)
            for link in role_module_permission_links
        }

        # Create a mapping of module id to the module object for easy lookup
        id_to_module = {m.id: m for m in filtered_modules}

        # For each module, filter its permissions based on the allowed permissions
        for module in filtered_modules:
            module.child_modules = []
            # Get only permission IDs and names for the allowed permissions
            module.permissions = [
                {"id": p.id, "name": p.name}
                for p in module.permissions
                if (module.id, p.id) in allowed_permissions
            ]

        # First pass: Build parent-child relationships
        for module in filtered_modules:
            if module.parent_module_id:
                parent = id_to_module.get(module.parent_module_id)
                if parent:
                    parent.child_modules.append(module)

        # Second pass: Find root modules (modules with no parent or parents not in the list)
        roots = []
        for module in filtered_modules:
            # Check if this module is a root (no parent) or if its parent is not in our list
            if not module.parent_module_id or module.parent_module_id not in id_to_module:
                roots.append(module)

        return [ModuleBasicResponse.model_validate(m, from_attributes=True) for m in roots]

    async def get_roles_by_ids(
        self, role_ids: list[str], client_id: str,
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
                    Roles.client_id == client_id,
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
                    role_metadata=role.meta_data,
                    modules=[],
                )
                for role in roles
            )

        # Get all module IDs that have permissions for any of the roles
        direct_module_ids = [link.module_id for link in role_module_permission_links]
        
        # First, fetch all modules that have direct permission links
        direct_modules_result = await self.session.scalars(
            select(Modules)
            .where(
                and_(
                    Modules.id.in_(direct_module_ids),
                    Modules.deleted_at.is_(None),
                    Modules.client_id == client_id,
                )
            )
            .options(selectinload(Modules.permissions), selectinload(Modules.child_modules))
        )
        direct_modules = list(direct_modules_result)
        
        # Get all parent module IDs from the direct modules
        parent_module_ids = set()
        for module in direct_modules:
            if module.parent_module_id:
                parent_module_ids.add(module.parent_module_id)
        
        # Fetch parent modules if they exist
        parent_modules = []
        if parent_module_ids:
            parent_modules_result = await self.session.scalars(
                select(Modules)
                .where(
                    and_(
                        Modules.id.in_(parent_module_ids),
                        Modules.deleted_at.is_(None),
                        Modules.client_id == client_id,
                    )
                )
                .options(selectinload(Modules.permissions), selectinload(Modules.child_modules))
            )
            parent_modules = list(parent_modules_result)
        
        # Combine all modules (direct + parent)
        all_modules = direct_modules + parent_modules

        if not all_modules:
            return role_response.extend(
                RoleResponse(
                    id=role.id,
                    name=role.name,
                    slug=role.slug,
                    description=role.description,
                    role_metadata=role.meta_data,
                    modules=[],
                )
                for role in roles
            )

        for role in roles:
            role_module_permission_links_for_role = [
                link
                for link in role_module_permission_links
                if link.role_id == role.id
            ]

            nested_modules = self.build_module_tree(
                all_modules, role_module_permission_links_for_role
            )

            role_response.append(
                RoleResponse(
                    id=role.id,
                    name=role.name,
                    slug=role.slug,
                    description=role.description,
                    role_metadata=role.meta_data,
                    modules=nested_modules,
                )
            )

        return role_response

    async def delete_role(self, role_id: str, client_id: str | None = None, user_id: str | None = None) -> SuccessResponse:
        """Delete a role by its slug.

        Args:
            role_id (str): The role id to delete.

        Returns:
            SuccessResponse: Success message.

        Raises:
            RoleNotFoundError: If the role is not found.
            RoleAssignedFoundError: If the role is assigned to users.
        """

        # Check if role is assigned to any users
        if await self.session.scalar(
            select(UserRoleLink).where(
                and_(
                    UserRoleLink.role_id == role_id,
                    UserRoleLink.client_id == client_id,
                )
            )
        ):
            raise RoleAssignedFoundError

        async with self.session.begin_nested():
            role = await self.session.get(Roles, role_id)
            if not role:
                raise RoleNotFoundError

            role.deleted_at = datetime.now(UTC).replace(tzinfo=None)
            role.deleted_by = user_id

        return SuccessResponse(message=RoleMessage.ROLE_DELETED)

    async def change_role_status(self, role_id: str, current_user_id: str) -> RoleStatusResponse:
        """
        Change the status of a role.
        """
        role = await self.session.scalar(
            select(Roles).where(
                and_(
                    Roles.id == role_id,
                    Roles.deleted_at.is_(None),
                )
            )
        )
        if not role:
            raise RoleNotFoundError

        if role.is_active:
            role.is_active = False
        else:
            role.is_active = True
        role.updated_by = current_user_id
        
        return RoleStatusResponse(
            id=role.id,
            is_active=role.is_active,
            message="Role status updated successfully",
        )