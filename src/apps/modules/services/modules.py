# """Service with methods to set and get values."""

# from typing import Annotated

# from fastapi import Depends
# from fastapi_pagination import Page, Params
# from sqlalchemy import and_, select
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import aliased, selectinload

# from apps.modules.constants import ModuleSortBy
# from apps.modules.models import ModulePermissionLink, Modules
# from apps.modules.schemas import ModuleResponse
# from core.constants import SortType
# from core.db import db_session
# from core.utils.pagination import paginate_array


# class ModuleService:
#     """Service with methods to set and get values."""

#     def __init__(
#         self,
#         session: Annotated[AsyncSession, Depends(db_session)],
#     ) -> None:
#         """Initialize service with db session and context.

#         Args:
#             session (AsyncSession): Database session
#         """
#         self.session = session

#     def build_module_tree(self, modules: list[Modules]) -> list[ModuleResponse]:
#         id_to_module = {m.id: m for m in modules}
#         for module in modules:
#             module.child_modules = []

#         roots = []
#         for module in modules:
#             if module.parent_module_id:
#                 parent = id_to_module.get(module.parent_module_id)
#                 if parent:
#                     parent.child_modules.append(module)
#                 else:
#                     # Parent not found in the current list → treat as root
#                     roots.append(module)
#             else:
#                 # No parent, definitely a root
#                 roots.append(module)

#         return [ModuleResponse.model_validate(r, from_attributes=True) for r in roots]

#     async def get_all_modules(
#     self,
#     params: Params,
#     sort_by: ModuleSortBy | None,
#     sort_type: SortType | None,
#     search: str | None = None,
# ) -> Page[ModuleResponse]:
#         """
#         Retrieve a paginated list of all modules, including child modules and permissions.

#         Args:
#             - params (Params): Pagination parameters (page number, size, etc.).
#             - sort_by (ModuleSortBy | None): Optional field name to sort the results by.
#             - sort_type (SortType | None): Optional sort direction (ascending or descending).
#             - search (str | None): Optional search keyword to filter modules by name or other attributes.

#         Returns:
#             - Page[ModuleResponse]: A paginated response containing modules, including child modules and permissions.
#         """
        
#         # Define the recursive CTE for module tree structure
#         base_query = select(Modules).where(
#             and_(
#                 Modules.parent_module_id.is_(None),  # Start from root modules
#                 Modules.deleted_at.is_(None),  # Exclude deleted modules
#             )
#         )

#         # Recursive part for fetching child modules
#         recursive_cte = base_query.cte(name="module_cte", recursive=True)

#         recursive_part = select(Modules).where(
#             and_(
#                 Modules.parent_module_id == recursive_cte.c.id,  # Parent-child relationship
#                 Modules.deleted_at.is_(None),  # Exclude deleted modules
#             )
#         )

#         module_cte = recursive_cte.union_all(recursive_part)

#         # Alias the CTE to use in the final query
#         m = aliased(Modules, module_cte)

#         final_query = select(m).select_from(module_cte)

#         # Join on the aliased CTE reference (ModulePermissionLink table)
#         final_query = final_query.outerjoin(
#             ModulePermissionLink, m.id == ModulePermissionLink.module_id
#         )

#         # Add search filter (optional)
#         if search:
#             final_query = final_query.where(m.name.ilike(f"%{search.strip()}%"))

#         # Sorting (optional)
#         if sort_by:
#             if sort_by == ModuleSortBy.NAME:
#                 final_query = final_query.order_by(
#                     m.name.asc() if sort_type == SortType.ASC else m.name.desc()
#                 )
#             elif sort_by == ModuleSortBy.CREATED_AT:
#                 final_query = final_query.order_by(
#                     m.created_at.asc() if sort_type == SortType.ASC else m.created_at.desc()
#                 )

#         # Load permissions and child modules (eager loading)
#         final_query = final_query.options(
#             selectinload(m.permissions),  # Eager load permissions
#             selectinload(m.child_modules),  # Eager load child modules (may be redundant if handled by recursive CTE)
#         )

#         # Execute the query to fetch the modules
#         result = await self.session.execute(final_query)
#         modules = result.scalars().unique().all()

#         # Build module tree (nest children under parents)
#         nested_modules = self.build_module_tree(modules)

#         # Paginate the result
#         return paginate_array(nested_modules, params)

from typing import Annotated
from fastapi import Depends
from fastapi_pagination import Page, Params
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload
from apps.modules.constants import ModuleSortBy
from apps.modules.models import ModulePermissionLink, Modules
from apps.modules.schemas import ModuleResponse
from core.constants import SortType
from core.db import db_session
from core.utils.pagination import paginate_array


class ModuleService:
    """Service with methods to set and get values."""

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
    ) -> None:
        """Initialize service with db session and context.

        Args:
            session (AsyncSession): Database session
        """
        self.session = session

    def build_module_tree(self, modules: list[Modules]) -> list[ModuleResponse]:
        """Builds a hierarchical tree structure for modules."""
        
        id_to_module = {m.id: m for m in modules}
        for module in modules:
            module.child_modules = []  # Initialize child modules as an empty list

        roots = []
        for module in modules:
            if module.parent_module_id:
                parent = id_to_module.get(module.parent_module_id)
                if parent:
                    parent.child_modules.append(module)  # Add as a child
                else:
                    # Parent not found → treat as root
                    roots.append(module)
            else:
                # Root module (no parent)
                roots.append(module)

        return [ModuleResponse.model_validate(r, from_attributes=True) for r in roots]

    async def get_all_modules(
        self,
        params: Params,
        sort_by: ModuleSortBy | None,
        sort_type: SortType | None,
        search: str | None = None,
    ) -> Page[ModuleResponse]:
        """
        Retrieve a paginated list of all modules, including child modules and permissions.
        
        Args:
            - params (Params): Pagination parameters (page number, size, etc.).
            - sort_by (ModuleSortBy | None): Optional field name to sort the results by.
            - sort_type (SortType | None): Optional sort direction (ascending or descending).
            - search (str | None): Optional search keyword to filter modules by name or other attributes.

        Returns:
            - Page[ModuleResponse]: A paginated response containing modules, including child modules and permissions.
        """
        
        # Define the recursive CTE for module tree structure
        base_query = select(Modules).where(
            and_(
                Modules.parent_module_id.is_(None),  # Start from root modules
                Modules.deleted_at.is_(None),  # Exclude deleted modules
            )
        )

        # Recursive part for fetching child modules
        recursive_cte = base_query.cte(name="module_cte", recursive=True)

        recursive_part = select(Modules).where(
            and_(
                Modules.parent_module_id == recursive_cte.c.id,  # Parent-child relationship
                Modules.deleted_at.is_(None),  # Exclude deleted modules
            )
        )

        module_cte = recursive_cte.union_all(recursive_part)

        # Alias the CTE to use in the final query
        m = aliased(Modules, module_cte)

        final_query = select(m).select_from(module_cte)

        # Join on the aliased CTE reference (ModulePermissionLink table)
        final_query = final_query.outerjoin(
            ModulePermissionLink, m.id == ModulePermissionLink.module_id
        )

        # Add search filter (optional)
        if search:
            final_query = final_query.where(m.name.ilike(f"%{search.strip()}%"))

        # Sorting (optional)
        if sort_by:
            if sort_by == ModuleSortBy.NAME:
                final_query = final_query.order_by(
                    m.name.asc() if sort_type == SortType.ASC else m.name.desc()
                )
            elif sort_by == ModuleSortBy.CREATED_AT:
                final_query = final_query.order_by(
                    m.created_at.asc() if sort_type == SortType.ASC else m.created_at.desc()
                )

        # Load permissions and child modules (eager loading)
        final_query = final_query.options(
            selectinload(m.permissions),  # Eager load permissions
            selectinload(m.child_modules),  # Eager load child modules
        )

        # Execute the query to fetch the modules
        result = await self.session.execute(final_query)
        modules = result.scalars().unique().all()

        # Build module tree (nest children under parents)
        nested_modules = self.build_module_tree(modules)

        # Paginate the result
        return paginate_array(nested_modules, params)
