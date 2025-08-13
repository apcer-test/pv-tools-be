"""Services for Users."""

from collections import defaultdict
from typing import Annotated, Any

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import EmailStr
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from apps.modules.schemas.response import ModuleResponse
from apps.roles.execeptions import RoleNotFoundError
from apps.roles.models import Roles
from apps.roles.services import RoleService
from apps.user_type.constants import UserTypeSortBy
from apps.user_type.execeptions import UserTypeNotFoundError
from apps.user_type.models import UserType
from apps.users.constants import (
    UserMessage,
    UserSortBy,
)
from apps.users.exceptions import (
    EmailAlreadyExistsError,
    PhoneAlreadyExistsError,
    UserNotFoundError,
)
from apps.users.models import UserRoleLink, Users
from apps.users.schemas.response import (
    BaseUserResponse,
    ListUserResponse,
    RoleResponse,
    UpdateUserResponse,
    UserResponse,
    UserTypeResponse,
)
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from apps.user.exceptions import EmailNotFoundError, UserNotFoundException
from apps.users.models.user import Users
from core.common_helpers import create_tokens
from core.db import db_session
from config import settings
from core.db import db_session, redis
from core.utils.datetime_utils import get_utc_now
from core.utils.resolve_context_ids import get_context_ids_from_keys
from core.utils.schema import SuccessResponse
from core.auth import access, refresh
from core.common_helpers import create_tokens
from config import settings
from fastapi.responses import RedirectResponse

class MicrosoftSSOService:
    """Service to handle Microsoft SSO authentication using Authlib"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize MicrosoftSSOService with database session

        Args:
            session: Database session for user operations
        """
        self.session = session

    async def sso_user(self, token: str, client_slug: str, **kwargs) -> dict[str, str]:
        """
        Handle Microsoft OAuth callback and authenticate user

        Args:
            token: Microsoft OAuth token
            kwargs: Additional keyword arguments

        Returns:
            dict with access and refresh tokens

        Raises:
            UserNotFoundException: If user with Microsoft email doesn't exist
        """
        try:
            email = kwargs.get("email")

            if not email:
                raise EmailNotFoundError

            user = await self.session.scalar(
                select(Users).where(Users.email == email)
            )

            if not user:
                raise UserNotFoundException

            res = await create_tokens(user_id=user.id, client_slug=client_slug)

            redirect_link = (
                f"{settings.LOGIN_REDIRECT_URL}?access-token={res.get('access_token')}&refresh-token="
                f"{res.get('refresh_token')}"
            )

            return RedirectResponse(url=redirect_link)
        except Exception as e:
            raise e


class UserService:
    """Service with methods to set and get values."""

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        role_service: Annotated[RoleService, Depends()],
        client_slug: str = None,
    ) -> None:
        self.session = session
        self.role_service = role_service
        self.client_id = None
        self.client_slug = client_slug
        self.redis = redis

    async def _resolve_context_ids(self) -> None:
        if self.client_id:
            return
        if not self.client_slug:
            raise ValueError("client_slug is required")
        client_id = await get_context_ids_from_keys(
            session=self.session, client_slug=self.client_slug
        )
        self.client_id = client_id

    def get_scopes_from_role(self, role: RoleResponse) -> list[dict[str, list[str]]]:
        """
        Given a role object, return a list of dicts with scopes and permissions.
        """
        scopes: list[dict[str, list[str]]] = []

        def process_module(module: ModuleResponse, scope_prefix: str = "") -> None:
            current_scope = module.name.lower().replace(" ", "-")
            full_scope = (
                f"{scope_prefix}:{current_scope}" if scope_prefix else current_scope
            )
            if hasattr(module, "permissions"):
                permissions = [
                    permission.name.lower().replace(" ", "-")
                    for permission in getattr(module, "permissions", [])
                ]
                if permissions:
                    scopes.append({"scope": full_scope, "permissions": permissions})
            for child in getattr(module, "child_modules", []):
                process_module(child, full_scope)

        for module in getattr(role, "modules", []):
            process_module(module)

        return scopes

    def get_merged_scopes_from_roles(
        self, roles: list[RoleResponse]
    ) -> list[dict[str, list[str]]]:
        """
        Given a list of role objects, return a merged
        list of dicts with scopes and combined permissions.
        """
        scope_permissions = defaultdict(set)

        def process_module(module: ModuleResponse, scope_prefix: str = "") -> None:
            current_scope = module.name.lower().replace(" ", "-")
            full_scope = (
                f"{scope_prefix}:{current_scope}" if scope_prefix else current_scope
            )
            permissions = [
                permission.name.lower().replace(" ", "-")
                for permission in getattr(module, "permissions", [])
            ]
            scope_permissions[full_scope].update(permissions)
            for child in getattr(module, "child_modules", []):
                process_module(child, full_scope)

        for role in roles:
            for module in getattr(role, "modules", []):
                process_module(module)

        return [
            {"scope": scope, "permissions": sorted(perms)}
            for scope, perms in scope_permissions.items()
        ]

    async def create_user(
        self,
        client_slug: str,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        role_ids: list[str] | None = None,
        user_type_id: str | None = None,
        description: str | None = None,
        user_metadata: dict | None = None,
    ) -> BaseUserResponse:
        """
        Creates a new user with the provided information.

         Args:
          - client_slug (str): The client slug means client_id or name. This is required.
          - username (str | None): The username of the user.
          - phone (str | None): The phone number of the user.
          - email (str | None): The email address of the user.
          - role_ids (list[str] | None) : List of role IDs to assign to the user.
          - user_type_id (str | None) : The Type ID of the user.
          - description (str | None): The description of the user.
          - meta_data (dict[str, Any] | None): The metadata of the user.

        Returns:
          - BaseUserResponse: A response containing the created user's basic information.

        Raises:
          - PhoneAlreadyExistsError: If the provided phone number already exists.
          - EmailAlreadyExistsError: If the provided email address already exists.
          - RoleNotFoundError: If any of the provided role IDs do not exist.
          - UserTypeNotFoundError: If the provided type ID does not exist.

        """

        if role_ids is None:
            role_ids = []
        self.client_slug = client_slug
        await self._resolve_context_ids()

        existing_user = await self.session.scalar(
            select(Users)
            .options(load_only(Users.phone, Users.email, Users.username))
            .where(
                and_(
                    Users.client_id == self.client_id,
                    or_(
                        and_(Users.phone == phone, Users.phone.is_not(None)),
                        and_(Users.email == email, Users.email.is_not(None)),
                    ),
                    Users.deleted_at.is_(None),
                )
            )
        )
        if existing_user:
            if phone and existing_user.phone == phone:
                raise PhoneAlreadyExistsError
            if email and existing_user.email == email:
                raise EmailAlreadyExistsError

        if len(role_ids) > 0:
            existing_roles_result = await self.session.scalars(
                select(Roles)
                .options(load_only(Roles.id))
                .where(
                    and_(
                        Roles.client_id == self.client_id,
                        Roles.id.in_(role_ids),
                        Roles.deleted_at.is_(None),
                    )
                )
            )
            existing_roles = list(existing_roles_result)
            if len(existing_roles) != len(role_ids):
                raise RoleNotFoundError

        if user_type_id:
            existing_usertype = await self.session.scalar(
                select(UserType)
                .options(load_only(UserType.id))
                .where(
                    and_(
                        UserType.client_id == self.client_id,
                        UserType.id == user_type_id,
                        UserType.deleted_at.is_(None),
                    )
                )
            )
            if not existing_usertype:
                raise UserTypeNotFoundError

        async with self.session.begin_nested():
            user = Users(
                username=username,
                phone=phone,
                email=email,
                user_type_id=user_type_id,
                client_id=self.client_id,
                description=description,
                user_metadata=user_metadata,
            )
            self.session.add(user)

        async with self.session.begin_nested():
            await self.session.refresh(user)

        async with self.session.begin_nested():
            for role_id in role_ids:
                user_role_link = UserRoleLink(
                    user_id=user.id,
                    role_id=role_id,
                    client_id=self.client_id,
                )
                self.session.add(user_role_link)

        return BaseUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            description=user.description,
            user_metadata=user.meta_data,
            role_ids=role_ids,
            user_type_id=user_type_id,
        )

    async def get_all_users(  # noqa: C901
        self,
        client_slug: str,
        page_param: Params,
        user: Users,
        user_ids: list[str] | None = None,
        username: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        role_slug: str | None = None,
        user_type_slug: str | None = None,
        is_active: bool | None = None,
        sortby: UserTypeSortBy | None = None,
    ) -> Page[ListUserResponse]:
        """
        Retrieves a paginated list of users with optional filtering and sorting.

        Args:
          - client_slug (str): The client slug means client_id or name. This is required.
          - param (Params): Pagination parameters including page number and size.
          - user_ids (list[str] | None): Optional list of user IDs to filter.
          - username (str | None): Optional filter by username.
          - email (str | None): Optional filter by email address.
          - phone (str | None): Optional filter by phone number.
          - role_slug (str | None): Optional filter by user role.
          - user_type_slug (str | None): Optional filter by user type.
          - is_active (bool | None): Optional filter by active status.
          - sortby (UserSortBy | None): Optional sorting field and direction.

        Returns:
          - Page[ListUserResponse]: A response containing the paginated list of users.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.

        """
        self.client_slug = client_slug
        await self._resolve_context_ids()

        query = (
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.username,
                    Users.email,
                    Users.phone,
                    Users.user_type_id,
                    Users.is_active,
                    Users.description,
                    Users.meta_data,
                ),
                selectinload(Users.user_type),
                selectinload(Users.roles),
            )
            .where(
                and_(
                    Users.client_id == self.client_id,
                    Users.deleted_at.is_(None),
                    Users.id != user.id,
                )
            )
        )

        if user_ids:
            query = query.where(Users.id.in_(user_ids))

        if username:
            query = query.where(Users.username.ilike(f"%{username}%"))

        if email:
            query = query.where(Users.email.ilike(f"%{email}%"))

        if phone:
            query = query.where(Users.phone.ilike(f"%{phone}%"))

        if role_slug:
            query = query.join(Roles).where(Roles.slug.ilike(f"%{role_slug}%"))

        if user_type_slug:
            query = query.join(UserType).where(UserType.slug.ilike(f"%{user_type_slug}%"))

        if is_active is not None:
            query = query.where(Users.is_active == is_active)

        if sortby in [UserSortBy.ROLE_DESC, UserSortBy.ROLE_ASC]:
            query = query.join(Roles, Users.roles.any(Roles.id == Roles.id))

        if sortby in [UserSortBy.USER_TYPE_DESC, UserSortBy.USER_TYPE_ASC]:
            query = query.join(UserType, Users.user_type_id == UserType.id)

        sort_options = {
            UserSortBy.NAME_DESC: Users.username.desc(),
            UserSortBy.NAME_ASC: Users.username.asc(),
            UserSortBy.EMAIL_DESC: Users.email.desc(),
            UserSortBy.EMAIL_ASC: Users.email.asc(),
            UserSortBy.ROLE_DESC: Roles.name.desc(),
            UserSortBy.ROLE_ASC: Roles.name.asc(),
            UserSortBy.USER_TYPE_DESC: UserType.name.desc(),
            UserSortBy.USER_TYPE_ASC: UserType.name.asc(),
        }

        sort_order = sort_options.get(sortby, Users.created_at.desc())
        query = query.order_by(sort_order)

        pagination = await paginate(self.session, query, page_param)
        items = [
            ListUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                roles=[RoleResponse(id=role.id, name=role.name) for role in user.roles],
                type=UserTypeResponse(
                    id=user.user_type.id if user.user_type else None,
                    name=user.user_type.name if user.user_type else None,
                ),
                is_active=user.is_active,
                description=user.description,
                user_metadata=user.meta_data,
            )
            for user in pagination.items
        ]
        pagination.items = items
        return pagination

    async def get_user_by_id(self, client_slug: str, user_id: str) -> ListUserResponse:
        """
        Retrieves detailed information about a specific user by their ID.

        Args:
            - client_slug (str): The client slug means client_id or name. This is required.
            - user_id (str): The unique identifier of the user to retrieve.

        Returns:
            - ListUserResponse: A response containing the user's information.

        Raises:
            - UserNotFoundError: If no user with the provided username is found.

        """
        self.client_slug = client_slug
        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.username,
                    Users.email,
                    Users.phone,
                    Users.user_type_id,
                    Users.is_active,
                    Users.description,
                    Users.meta_data,
                ),
                selectinload(Users.user_type),
                selectinload(Users.roles),
            )
            .where(
                and_(
                    Users.client_id == self.client_id,
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not user:
            raise UserNotFoundError
        return ListUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            description=user.description,
            user_metadata=user.meta_data,
            roles=[RoleResponse(id=role.id, name=role.name) for role in user.roles],
            type=UserTypeResponse(
                id=user.user_type.id if user.user_type else None,
                name=user.user_type.name if user.user_type else None,
            ),
            is_active=user.is_active,
        )

    async def change_user_status(self, client_slug: str, user_id: str) -> Users:
        """
        Toggles the active status of a user by their ID.

        Args:
          - client_slug (str): The client slug means client_id or name. This is required.
          - user_id (str): The ID of the user whose status is to be changed.

        Returns:
          - Users: A response indicating the user's updated status.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.

        """
        self.client_slug = client_slug
        await self._resolve_context_ids()

        existing_user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.username,
                    Users.phone,
                    Users.email,
                    Users.is_active,
                )
            )
            .where(
                and_(
                    Users.client_id == self.client_id,
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not existing_user:
            raise UserNotFoundError

        if existing_user.is_active:
            existing_user.is_active = False
        else:
            existing_user.is_active = True

        return existing_user

    async def _assign_user_roles(
        self, session: AsyncSession, user_id: str, role_ids: list[str]
    ) -> None:
        """Synchronize user roles with the provided role_ids."""
        # Fetch current role links for the user
        existing_links = await session.scalars(
            select(UserRoleLink).where(UserRoleLink.user_id == user_id)
        )
        existing_links = list(existing_links)
        existing_role_ids = {link.role_id for link in existing_links}

        # Roles to remove
        to_remove = [link for link in existing_links if link.role_id not in role_ids]
        # Roles to add
        to_add = [role_id for role_id in role_ids if role_id not in existing_role_ids]

        # Remove unneeded links
        for link in to_remove:
            await session.delete(link)

        # Add new links
        for role_id in to_add:
            link = UserRoleLink(
                user_id=user_id,
                role_id=role_id,
                client_id=self.client_id,
            )
            session.add(link)

    async def update(  # noqa: C901
        self,
        client_slug: str,
        user_id: str,
        username: str | None = None,
        email: EmailStr | None = None,
        phone: str | None = None,
        role_ids: list[str] | None = None,
        user_type_id: str | None = None,
        description: str | None = None,
        user_metadata: dict[str, Any] | None = None,
    ) -> UpdateUserResponse:
        """
        Updates the information of a specific user by their ID.

        Args:
            - client_slug (str): The client slug means client_id or name. This is required.
          - user_id (str): The unique identifier of the user to retrieve.
          - username (str | None): The username of the user.
          - phone (str | None): The phone number of the user.
          - email (str | None): The email address of the user.
          - role_ids (list[str] | None) : List of role IDs to assign to the user.
          - user_type_id (str | None) : The Type ID of the user.
          - description (str | None): The description of the user.

        Returns:
          - UpdateUserResponse: A response containing the updated user data.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.
          - PhoneAlreadyExistsError: If the provided phone number already exists.
          - EmailAlreadyExistsError: If the provided email address already exists.
          - RoleNotFoundError: If the provided role ID does not exist.
          - UserTypeNotFoundError: If the provided user type ID does not exist.

        """
        self.client_slug = client_slug
        await self._resolve_context_ids()

        async with self.session.begin_nested():
            existing_user = await self.session.scalar(
                select(Users)
                .options(
                                    load_only(
                    Users.id,
                    Users.username,
                    Users.phone,
                    Users.email,
                    Users.user_type_id,
                    Users.description,
                    Users.meta_data,
                ),
                    selectinload(Users.roles),
                )
                .where(
                    and_(
                        Users.client_id == self.client_id,
                        Users.id == user_id,
                        Users.deleted_at.is_(None),
                    )
                )
            )
            if not existing_user:
                raise UserNotFoundError

            if phone:
                existing_phone = await self.session.scalar(
                    select(Users.id).where(
                        and_(
                            Users.client_id == self.client_id,
                            Users.phone == phone,
                            Users.id != user_id,
                        )
                    )
                )
                if existing_phone:
                    raise PhoneAlreadyExistsError
            if email:
                existing_email = await self.session.scalar(
                    select(Users.id).where(
                        and_(
                            Users.client_id == self.client_id,
                            Users.email == email,
                            Users.id != user_id,
                        )
                    )
                )
                if existing_email:
                    raise EmailAlreadyExistsError
            roles = existing_user.roles
            if role_ids:
                roles_result = await self.session.scalars(
                    select(Roles)
                    .options(load_only(Roles.id, Roles.name))
                    .where(
                        and_(
                            Roles.client_id == self.client_id,
                            Roles.id.in_(role_ids),
                            Roles.deleted_at.is_(None),
                        )
                    )
                )
                existing_roles = roles_result.all()
                if len(existing_roles) != len(role_ids):
                    raise RoleNotFoundError
                await self._assign_user_roles(self.session, user_id, role_ids)
                roles = existing_roles

            if user_type_id:
                existing_usertype = await self.session.scalar(
                    select(UserType)
                    .options(load_only(UserType.id))
                    .where(
                        and_(
                            UserType.client_id == self.client_id,
                            UserType.id == user_type_id,
                            UserType.deleted_at.is_(None),
                        )
                    )
                )
                if not existing_usertype:
                    raise UserTypeNotFoundError

            existing_user.username = (
                username if username is not None else existing_user.username
            )
            existing_user.phone = phone if phone is not None else existing_user.phone
            existing_user.email = email if email is not None else existing_user.email
            existing_user.description = (
                description if description is not None else existing_user.description
            )
            existing_user.meta_data = (
                user_metadata
                if user_metadata is not None
                else existing_user.meta_data
            )
            existing_user.user_type_id = (
                user_type_id if user_type_id is not None else existing_user.user_type_id
            )

            return UpdateUserResponse(
                id=existing_user.id,
                username=existing_user.username,
                email=existing_user.email,
                phone=existing_user.phone,
                description=existing_user.description,
                user_metadata=existing_user.meta_data,
                roles=[RoleResponse(id=role.id, name=role.name) for role in roles],
                user_type_id=existing_user.user_type_id,
            )

    async def delete(self, client_slug: str, user_id: str) -> SuccessResponse:
        """
        Deletes a user account by their ID.

        Args:
          - client_slug (str): The client slug means client_id or name. This is required.
          - user_id (str): The ID of the user whose status is to be changed.

        Returns:
          - SuccessResponse: A response indicating successful deletion of the user.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.
        """
        self.client_slug = client_slug
        await self._resolve_context_ids()

        existing_user = await self.session.scalar(
            select(Users)
            .options(load_only(Users.id, Users.username, Users.email, Users.phone))
            .where(
                and_(
                    Users.client_id == self.client_id,
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not existing_user:
            raise UserNotFoundError

        existing_user.deleted_at = get_utc_now()

        return SuccessResponse(message=UserMessage.USER_DELETED)

    async def get_self(self, client_slug: str, user_id: str) -> UserResponse:
        """
        Retrieves the profile information of the currently authenticated user.

        Args:
          - client_slug (str): The client slug means client_id or name. This is required.

        Returns:
          - UserResponse: A response containing the user's profile information.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.

        """
        self.client_slug = client_slug
        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                selectinload(Users.user_type),
                selectinload(Users.roles),
            )
            .where(
                Users.client_id == self.client_id,
                Users.id == user_id,
            )
        )
        if not user:
            raise UserNotFoundError

        role_ids = [link.id for link in user.roles]

        roles = []
        if role_ids:
            roles = await self.role_service.get_roles_by_ids(
                role_ids=role_ids,
                client_id=self.client_id,
            )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            description=user.description,
            user_metadata=user.meta_data,
            roles=roles,
            type=(
                UserTypeResponse(id=user.user_type.id, name=user.user_type.name)
                if user.user_type
                else None
            ),
            created_at=user.created_at,
            updated_at=user.updated_at,
            mfa_enabled=False,  # Default value since field doesn't exist in model
            mfa_enrolled=False,  # Default value since field doesn't exist in model
        )