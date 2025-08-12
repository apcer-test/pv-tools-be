"""Service with methods to set and get values."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Path
from fastapi_pagination import Page, Params
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload, load_only, selectinload
from sqlalchemy.orm import aliased, joinedload, load_only, selectinload

from apps.modules.constants import ModuleMessage, ModuleSortBy
from apps.modules.execeptions import (
    ModuleAlreadyExistsError,
    ModuleAssignedFoundError,
    ModuleNotFoundCustomError,
)
from apps.modules.models import ModulePermissionLink, Modules
from apps.modules.schemas import ModuleResponse
from apps.permissions.execeptions import PermissionNotFoundError
from apps.permissions.models import Permissions
from apps.roles.models import RoleModulePermissionLink
from core.constants import SortType
from core.db import db_session
from core.utils.pagination import paginate_array
from core.utils.pagination import paginate_array
from core.utils.resolve_context_ids import get_context_ids_from_keys
from core.utils.schema import SuccessResponse
from core.utils.slug_utils import (
    generate_unique_slug,
    validate_and_generate_slug,
    validate_unique_slug,
)


class ModuleService:
    """Service with methods to set and get values."""

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        tenant_key: Annotated[int | str, Path()],
        app_key: Annotated[int | str, Path()],
    ) -> None:
        """Initialize service with db session and context.

        Args:
            session (AsyncSession): Database session
            app_id (int): Application ID
            tenant_id (int): Tenant ID
        """
        self.session = session
        self.app_key = app_key
        self.tenant_key = tenant_key
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

    async def _resolve_module_id(self, module_key: str | int) -> int:
        try:
            query = Modules.id == int(module_key)
        except (ValueError, TypeError):
            query = Modules.slug == module_key

        module_id = await self.session.scalar(
            select(Modules.id).where(
                and_(
                    query,
                    Modules.tenant_id == self.tenant_id,
                    Modules.app_id == self.app_id,
                    Modules.deleted_at.is_(None),
                )
            )
        )
        if not module_id:
            raise ModuleNotFoundCustomError

        return module_id

    async def create_modules(
        self,
        name: str,
        slug: str | None,
        parent_module_id: int | None,
        permissions: list[int] | None,
        description: str | None = None,
        module_metadata: dict | None = None,
    ) -> Modules:
        """
        Create a new module.

        Args:
            - name (str): The name of the module.
            - slug (str | None): Optional slug for the module used for referencing
            or URL-friendly names.
            - parent_module_id (int | None) : Optional parent module ID to assign to
            the module.
            - permissions (list[int] | None): Optional list of permission IDs to assign
            to the module.
            - description (str | None): Optional description of the module.
            - module_metadata (dict | None): Optional metadata for the module.

        Returns:
          - Modules: ModuleModel for the created module.

        Raises:
          - ModuleAlreadyExistsError: If a module with the same name already exists.
          - PermissionNotFoundError: If a permission with the given ID is not found
          or a permission.
          - PermissionNotFoundError: If a permission with the given ID is not found
          or a permission.
        """
        await self._resolve_context_ids()

        async with self.session.begin_nested():
            if await self.session.scalar(
                select(Modules)
                .options(load_only(Modules.name))
                .where(
                    and_(
                        Modules.name.ilike(name),
                        Modules.tenant_id == self.tenant_id,
                        Modules.app_id == self.app_id,
                        Modules.deleted_at.is_(None),
                    )
                )
            ):
                raise ModuleAlreadyExistsError

        if permissions:
            existing_permissions = await self.session.scalars(
                select(Permissions)
                .options(load_only(Permissions.id))
                .where(
                    and_(
                        Permissions.tenant_id == self.tenant_id,
                        Permissions.app_id == self.app_id,
                        Permissions.id.in_(permissions),
                        Permissions.deleted_at.is_(None),
                    )
                )
            )
            existing_permissions = list(existing_permissions)
            if len(existing_permissions) != len(permissions):
                raise PermissionNotFoundError

        slug = await validate_and_generate_slug(
            slug=slug,
            name=name,
            db=self.session,
            model=Modules,
            tenant_id=self.tenant_id,
            app_id=self.app_id,
        )

        async with self.session.begin_nested():
            module = Modules(
                name=name,
                slug=slug,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                parent_module_id=parent_module_id,
                description=description,
                module_metadata=module_metadata,
            )
            if parent_module_id:
                module.permissions = []
            self.session.add(module)

        if permissions:
            async with self.session.begin_nested():
                for permission_id in permissions:
                    module_permission_link = ModulePermissionLink(
                        tenant_id=self.tenant_id,
                        app_id=self.app_id,
                        module_id=module.id,
                        permission_id=permission_id,
                    )
                    self.session.add(module_permission_link)

        async with self.session.begin_nested():
            await self.session.refresh(
                module, attribute_names=["permissions", "child_modules"]
            )

        return module

    async def get_all_modules(
        self,
        params: Params,
        sort_by: ModuleSortBy | None,
        sort_type: SortType | None,
        search: str | None = None,
    ) -> Page[Modules]:
        """
        Retrieve a paginated list of modules.

        Args:
            - params (Params): Pagination parameters (page number, size, etc.).
            - sort_by (ModuleSortBy | None): Optional field name to sort the results by.
            - sort_type (SortType | None): Optional sort direction
            (ascending or descending).
            - search (str | None): Optional search keyword to filter modules by name
            or other attributes.

        Returns:
            - Page[Modules]: A response containing a paginated list of modules.

        """

        await self._resolve_context_ids()

        # Define the recursive CTE
        base_query = select(Modules).where(
            and_(
                Modules.tenant_id == self.tenant_id,
                Modules.app_id == self.app_id,
                Modules.parent_module_id.is_(None),
                Modules.deleted_at.is_(None),
            )
        )

        # Recursive part
        recursive_cte = base_query.cte(name="module_cte", recursive=True)

        recursive_part = select(Modules).where(
            and_(
                Modules.parent_module_id == recursive_cte.c.id,
                Modules.deleted_at.is_(None),
            )
        )

        module_cte = recursive_cte.union_all(recursive_part)

        # Alias the CTE to use in the final query
        m = aliased(Modules, module_cte)

        final_query = select(m).select_from(module_cte)

        # Join on the aliased CTE reference
        final_query = final_query.outerjoin(
            ModulePermissionLink, m.id == ModulePermissionLink.module_id
        )

        # Add search filter
        if search:
            final_query = final_query.where(m.name.ilike(f"%{search.strip()}%"))

        # Sorting
        if sort_by:
            if sort_by == ModuleSortBy.NAME:
                final_query = final_query.order_by(
                    m.name.asc() if sort_type == SortType.ASC else m.name.desc()
                )
            elif sort_by == ModuleSortBy.CREATED_AT:
                final_query = final_query.order_by(
                    m.created_at.asc()
                    if sort_type == SortType.ASC
                    else m.created_at.desc()
                )

        # Load permissions
        final_query = final_query.options(
            selectinload(m.permissions), selectinload(m.child_modules)
        )

        result = await self.session.execute(final_query)
        modules = result.scalars().unique().all()
        nested = self.build_module_tree(modules)

        return paginate_array(nested, params)

    def build_module_tree(self, modules: list[Modules]) -> list[ModuleResponse]:
        id_to_module = {m.id: m for m in modules}
        for module in modules:
            module.child_modules = []

        roots = []
        for module in modules:
            if module.parent_module_id:
                parent = id_to_module.get(module.parent_module_id)
                if parent:
                    parent.child_modules.append(module)
                else:
                    # Parent not found in the current list → treat as root
                    roots.append(module)
            else:
                # No parent, definitely a root
                roots.append(module)

        return [ModuleResponse.model_validate(r, from_attributes=True) for r in roots]

    async def get_module_by_id(self, module_key: int) -> Modules:
        """
        Retrieve a specific module by its key.

        Args:
          - tenant_key (int/str): The KEY of the tenant to which the permission belongs.
          This is required.
          - app_key (int/str): The KEY of the application to which the permission
          belongs. This is required.
          - module_key (int | str): Unique identifier of the module
          (could be an ID or key).

        Returns:
           Modules: A standardized response containing the module's details.

        Raises:
            ModuleNotFoundError: If the module is not found.
        """
        await self._resolve_context_ids()
        module_id = await self._resolve_module_id(module_key=module_key)

        # Base query: start from the target module
        base_query = select(Modules).where(
            and_(
                Modules.id == module_id,
                Modules.tenant_id == self.tenant_id,
                Modules.app_id == self.app_id,
                Modules.deleted_at.is_(None),
            )
        )

        # Recursive CTE setup: find all descendants
        recursive_cte = base_query.cte(name="module_cte", recursive=True)

        recursive_part = select(Modules).where(
            and_(
                Modules.parent_module_id == recursive_cte.c.id,
                Modules.deleted_at.is_(None),
            )
        )

        module_cte = recursive_cte.union_all(recursive_part)

        # Alias for final query
        m = aliased(Modules, module_cte)

        final_query = (
            select(m)
            .select_from(module_cte)
            # Join permission links if you want permissions
            .outerjoin(ModulePermissionLink, m.id == ModulePermissionLink.module_id)
            .options(
                selectinload(m.permissions),  # eager load permissions
                selectinload(
                    m.child_modules
                ),  # eager load child modules (may be redundant)
            )
        )

        # Execute query and fetch all related modules (target + descendants)
        result = await self.session.execute(final_query)
        modules = result.scalars().unique().all()
        if not modules:
            raise ModuleNotFoundCustomError

        # Build tree to nest children under parents
        nested = self.build_module_tree(modules)

        # Root module with children (there should be exactly one root: the module_id)
        # If you want just the single root module object:
        root_module = next((m for m in nested if m.id == module_id), None)
        if root_module is None:
            raise ModuleNotFoundCustomError

        return root_module

    async def delete_module(self, module_key: int | str) -> SuccessResponse:
        """
        Delete a module by its key.

        Args:
          - module_key (int | str): Unique identifier of the module to be deleted.

        Returns:
          - SuccessResponse: A standardized response indicating successful deletion.

        Raises:
          - ModuleNotFoundError: If the module to be deleted is not found.
          - ModuleAssignedFoundError: If the module is assigned to any users.
        """

        await self._resolve_context_ids()
        module_id = await self._resolve_module_id(module_key=module_key)

        existing_module = await self.session.scalar(
            select(Modules)
            .options(load_only(Modules.id, Modules.name))
            .where(
                and_(
                    Modules.tenant_id == self.tenant_id,
                    Modules.app_id == self.app_id,
                    Modules.id == module_id,
                    Modules.deleted_at.is_(None),
                )
            )
        )
        if not existing_module:
            raise ModuleNotFoundCustomError

        all_users_with_permission = await self.session.scalars(
            select(RoleModulePermissionLink)
            .options(load_only(RoleModulePermissionLink.id))
            .where(
                and_(
                    RoleModulePermissionLink.module_id == module_id,
                    RoleModulePermissionLink.deleted_at.is_(None),
                )
            )
        )
        user_list_with_permission = [per.id for per in all_users_with_permission]
        if user_list_with_permission:
            raise ModuleAssignedFoundError

        existing_module.deleted_at = datetime.now(UTC).replace(tzinfo=None)

        return SuccessResponse(message=ModuleMessage.MODULE_DELETED)

    async def update_module(
        self,
        module_key: int | str,
        name: str,
        parent_module_id: int | None,
        permissions: list[int] | None,
        slug: str | None,
        description: str | None = None,
        module_metadata: dict | None = None,
    ) -> Modules:
        """
        Update an existing module.

        Args:
          - module_key (int | str): Unique identifier of the module to be updated.
          - name (str): The name of the module.
          - parent_module_id (int | None) : Optional parent module ID
          to assign to the module.
          - permissions (list[int] | None): Optional list of permission IDs
          to assign to the module.
          - slug (str | None): Optional slug for the module used for
          referencing or URL-friendly names.
          - description (str | None): Optional description of the module.
          - module_metadata (dict | None): Optional metadata for the module.

        Returns:
          - Modules: A ModuleModel containing the updated module's information.

        Raises:
            ModuleNotFoundError: If the module to be updated is not found.
            ModuleAlreadyExistsError: If a module with the same name already exists.
            PermissionNotFoundError: If a permission with the given ID is not
            found or a permission.
        """

        await self._resolve_context_ids()
        module_id = await self._resolve_module_id(module_key=module_key)

        # Check if module exists
        module = await self.session.scalar(
            select(Modules)
            .options(joinedload(Modules.child_modules).joinedload(Modules.permissions))
            .where(
                and_(
                    Modules.id == module_id,
                    Modules.tenant_id == self.tenant_id,
                    Modules.app_id == self.app_id,
                    Modules.deleted_at.is_(None),
                )
            )
        )
        if not module:
            raise ModuleNotFoundCustomError

        module.parent_module_id = parent_module_id

        # Check if name is already taken
        if await self.session.scalar(
            select(Modules).where(
                and_(
                    Modules.id != module_id,
                    Modules.name.ilike(name),
                    Modules.parent_module_id == module.parent_module_id,
                    Modules.tenant_id == self.tenant_id,
                    Modules.app_id == self.app_id,
                    Modules.deleted_at.is_(None),
                )
            )
        ):
            raise ModuleAlreadyExistsError

        if slug and module.slug != slug:
            await validate_unique_slug(
                slug,
                db=self.session,
                model=Modules,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
            )
            module.slug = slug
        elif module.name != name:
            module.slug = await generate_unique_slug(
                name,
                db=self.session,
                model=Modules,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                existing_id=module.id,
            )

        # Update module with new values
        module.name = name
        if description is not None:
            module.description = description
        if module_metadata is not None:
            module.module_metadata = module_metadata
        module.updated_at = datetime.now(UTC).replace(tzinfo=None)
        if permissions:
            async with self.session.begin_nested():
                existing_module_permissions = await self.session.scalars(
                    select(Permissions)
                    .options(load_only(Permissions.id))
                    .where(
                        and_(
                            Permissions.tenant_id == self.tenant_id,
                            Permissions.app_id == self.app_id,
                            Permissions.deleted_at.is_(None),
                            Permissions.id.in_(permissions),
                        )
                    )
                )
                existing_module_permissions = list(existing_module_permissions)
                if len(existing_module_permissions) != len(permissions):
                    raise PermissionNotFoundError

            async with self.session.begin_nested():
                module_permissions = await self.session.scalars(
                    select(ModulePermissionLink)
                    .options(load_only(ModulePermissionLink.permission_id))
                    .where(
                        and_(
                            ModulePermissionLink.module_id == module_id,
                            ModulePermissionLink.deleted_at.is_(None),
                        )
                    )
                )
                module_permissions_list = [
                    permission.permission_id for permission in module_permissions
                ]
                module_permissions_set = set(module_permissions_list)
                permissions_to_delete = module_permissions_set - set(permissions)
                module_permissions_to_delete = await self.session.scalars(
                    select(ModulePermissionLink).where(
                        and_(
                            ModulePermissionLink.permission_id.in_(
                                permissions_to_delete
                            ),
                            ModulePermissionLink.deleted_at.is_(None),
                        )
                    )
                )
                for module_permission in module_permissions_to_delete.all():
                    module_permission.deleted_at = datetime.now(UTC).replace(
                        tzinfo=None
                    )
                permissions_to_add = set(permissions) - module_permissions_set
                for permission_id in permissions_to_add:
                    module_permission_link = ModulePermissionLink(
                        tenant_id=self.tenant_id,
                        app_id=self.app_id,
                        module_id=module.id,
                        permission_id=permission_id,
                    )
                    self.session.add(module_permission_link)

        async with self.session.begin_nested():
            await self.session.refresh(
                module, attribute_names=["permissions", "child_modules"]
            )

        return module
