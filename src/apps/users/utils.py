from typing import Annotated, Any, Callable

from fastapi import Request, status
from fastapi.exceptions import HTTPException
from fastapi.params import Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.clients.models.clients import Clients
from apps.modules.models import Modules
from apps.permissions.models.permissions import Permissions
from apps.roles.models.roles import RoleModulePermissionLink
from apps.users.models import UserRoleLink, Users
from core.auth import access
from core.constants import ErrorMessage
from core.db import db_session
from core.exceptions import BadRequestError, ForbiddenError, UnauthorizedError


async def current_user(
    token_claims: Annotated[dict[str, Any], Depends(access)],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> dict[str, Any]:
    """Fetch the client user and return it.

    :param token_claims: The token payload.
    :param session: The database session.

    :return: Dictionary containing user object and client_id.
    """

    # First, verify the user exists and has access to the specified client
    user = await session.scalar(
        select(Users).where(
            Users.id == token_claims.get("id"),
            Users.clients.any(Clients.id == token_claims.get("client_id")),
        )
    )

    if not user:
        raise UnauthorizedError(message=ErrorMessage.UNAUTHORIZED)

    return {"user": user, "client_id": token_claims.get("client_id")}


# Map HTTP methods to required permission slugs
HTTP_METHOD_PERMISSION_MAP: dict[str, str] = {
    "GET": "view",
    "POST": "edit",
    "PUT": "edit",
    "PATCH": "edit",
    "DELETE": "delete",
}


def permission_required(
    main_modules: list[str], sub_modules: list[str]
) -> Callable[..., Any]:
    """Dependency to enforce module/sub-module permission for current user.

    Usage:
        @router.patch(
            "/{item_id}",
            dependencies=[Depends(permission_required(["Role"], ["Role Management"]))],
        )
    """

    if len(main_modules) != len(sub_modules):
        raise BadRequestError(
            message="The number of main modules must match the number of submodules."
        )

    async def verify_permissions(
        request: Request,
        session: Annotated[AsyncSession, Depends(db_session)],
        user_ctx: Annotated[dict[str, Any], Depends(current_user)],
    ) -> bool:
        """Verify if the user has the required permissions to access the resource."""

        required_permission_slug = HTTP_METHOD_PERMISSION_MAP.get(request.method)
        if not required_permission_slug:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=f"Unsupported HTTP method: {request.method}",
            )

        user = user_ctx.get("user")
        client_id = user_ctx.get("client_id")
        if not user or not client_id:
            raise UnauthorizedError(message=ErrorMessage.UNAUTHORIZED)

        # Resolve required permission id within client
        permission_id = await session.scalar(
            select(Permissions.id).where(
                and_(
                    Permissions.slug == required_permission_slug,
                    Permissions.client_id == client_id,
                    Permissions.deleted_at.is_(None),
                )
            )
        )
        if not permission_id:
            # Permission configuration missing for client
            raise ForbiddenError(
                message=f"Permission '{required_permission_slug}' is not configured for this client"
            )

        # Fetch role ids for this user in this client
        role_ids_result = await session.scalars(
            select(UserRoleLink.role_id).where(
                and_(
                    UserRoleLink.user_id == user.id,
                    UserRoleLink.client_id == client_id,
                    UserRoleLink.deleted_at.is_(None),
                )
            )
        )
        role_ids = [rid for rid in role_ids_result]
        if not role_ids:
            raise ForbiddenError(message="No role assigned to the user")

        # Batch-resolve all needed modules (parents and children) in a single query
        unique_main_slugs = set(main_modules)
        unique_sub_slugs = set(sub_modules)
        all_slugs = list(unique_main_slugs | unique_sub_slugs)

        if not all_slugs:
            return True

        modules_result = await session.execute(
            select(Modules.id, Modules.slug, Modules.parent_module_id).where(
                and_(
                    Modules.client_id == client_id,
                    Modules.slug.in_(all_slugs),
                    Modules.deleted_at.is_(None),
                )
            )
        )
        rows = modules_result.all()
        # Build lookup maps
        slug_to_id: dict[str, str] = {row[1]: row[0] for row in rows}
        slug_to_parent_id: dict[str, str | None] = {row[1]: row[2] for row in rows}

        # Validate parent/child relationships and collect child module ids to check permissions for
        child_module_ids: list[str] = []
        for main_module_name, sub_module_name in zip(main_modules, sub_modules):
            parent_module_id = slug_to_id.get(main_module_name)
            if not parent_module_id:
                raise ForbiddenError(
                    message=f"Module '{main_module_name}' not assigned to this user"
                )

            child_id = slug_to_id.get(sub_module_name)
            child_parent_id = slug_to_parent_id.get(sub_module_name)
            if not child_id or child_parent_id != parent_module_id:
                raise ForbiddenError(
                    message=f"Sub-module '{sub_module_name}' under '{main_module_name}' not assigned to this user"
                )

            child_module_ids.append(child_id)

        # Batch check permission links for all child modules in one query
        permitted_module_ids_result = await session.scalars(
            select(RoleModulePermissionLink.module_id).where(
                and_(
                    RoleModulePermissionLink.role_id.in_(role_ids),
                    RoleModulePermissionLink.module_id.in_(child_module_ids),
                    RoleModulePermissionLink.permission_id == permission_id,
                    RoleModulePermissionLink.client_id == client_id,
                    RoleModulePermissionLink.deleted_at.is_(None),
                )
            )
        )
        permitted_module_ids = set([mid for mid in permitted_module_ids_result])

        # Ensure each requested sub-module has the required permission for at least one of the user's roles
        for main_module_name, sub_module_name in zip(main_modules, sub_modules):
            child_id = slug_to_id[sub_module_name]
            if child_id not in permitted_module_ids:
                raise ForbiddenError(
                    message=f"Permission '{required_permission_slug}' required for '{sub_module_name}'"
                )

        return True

    return verify_permissions
