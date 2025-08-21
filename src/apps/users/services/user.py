"""Services for Users."""

import copy
import json
from datetime import datetime
from io import BytesIO
from typing import Annotated, Any, Optional

from fastapi import Depends, Request, status
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import EmailStr
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload
from starlette.responses import JSONResponse, RedirectResponse, StreamingResponse

from apps.clients.models.clients import Clients
from apps.modules.models.modules import Modules
from apps.roles.execeptions import RoleNotFoundError
from apps.roles.models import Roles
from apps.roles.models.roles import RoleModulePermissionLink
from apps.roles.schemas.response import ModuleBasicResponse
from apps.roles.services import RoleService
from apps.users.constants import UserSortBy
from apps.users.exceptions import (
    EmailAlreadyExistsError,
    EmailNotFoundError,
    PhoneAlreadyExistsError,
    UserDuplicateClientAssignmentError,
    UserNotFoundError,
    UserNotFoundException,
)
from apps.users.models import UserRoleLink, Users
from apps.users.models.user import LoginActivity
from apps.users.schemas.request import LoginActivityCreate, UserClientAssignment
from apps.users.schemas.response import (
    AssignUserClientsResponse,
    ClientResponse,
    CreateUserResponse,
    ListUserResponse,
    LoginActivityOut,
    RoleResponse,
    UpdateUserResponse,
    UserAssignmentsResponse,
    UserClientAssignmentResponse,
    UserSelfResponse,
    UserSelfRoleResponse,
    UserStatusResponse,
)
from config import settings
from constants.messages import INVALID_TOKEN, SUCCESS, UNAUTHORIZED
from core.auth import access
from core.common_helpers import create_tokens
from core.db import db_session, redis
from core.exceptions import InvalidJWTTokenException, UnauthorizedError
from core.types import LoginActivityStatus
from core.utils.hashing import Hash
from core.utils.login_logger import log_login_activity
from core.utils.set_cookies import create_user_token_caching


class MicrosoftSSOService:
    """Service to handle Microsoft SSO authentication using Authlib"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize MicrosoftSSOService with database session

        Args:
            session: Database session for user operations
        """
        self.session = session

    async def sso_user(
        self, client_slug: str, request: Request, **kwargs
    ) -> dict[str, str]:
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
                select(Users)
                .options(selectinload(Users.roles))
                .join(UserRoleLink, Users.id == UserRoleLink.user_id)
                .where(
                    and_(
                        Users.email == email,
                        Users.deleted_at.is_(None),
                        UserRoleLink.client_id == client_slug,
                    )
                )
            )

            if not user:
                await log_login_activity(
                    self.session,
                    LoginActivityCreate(
                        user_id=None,
                        client_id=client_slug,
                        status=LoginActivityStatus.FAILED,
                        activity="System Login",
                        reason=f"Failed to login, user not found: {email}",
                        ip_address=request.client.host,
                    ),
                )
                raise UserNotFoundException

            if user.is_active is False:
                await log_login_activity(
                    self.session,
                    LoginActivityCreate(
                        user_id=user.id,
                        client_id=client_slug,
                        status=LoginActivityStatus.FAILED,
                        activity="System Login",
                        reason=f"Failed to login, user is not active: {email}",
                        ip_address=request.client.host,
                    ),
                )
                raise UnauthorizedError

            res = await create_tokens(user_id=user.id, client_slug=client_slug)
            access_token = res.get("access_token")
            refresh_token = res.get("refresh_token")
            await create_user_token_caching(
                tokens={"access_token": access_token, "refresh_token": refresh_token},
                user_id=user.id,
                client_slug=client_slug,
            )

            redirect_link = f"{settings.LOGIN_REDIRECT_URL}?accessToken={access_token}&refreshToken={refresh_token}"
            await log_login_activity(
                self.session,
                LoginActivityCreate(
                    user_id=user.id,
                    client_id=client_slug,
                    status=LoginActivityStatus.SUCCESS,
                    activity="System Login",
                    reason="User logged in successfully",
                    ip_address=request.client.host,
                ),
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
    ) -> None:
        self.session = session
        self.role_service = role_service

    async def create_user(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        user_id: str | None = None,
    ) -> CreateUserResponse:
        """
        Creates a new user with only basic information.

        Args:
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            phone (str): The user's phone number.
            email (str): The user's email address.
            user_id (str | None): The ID of the user who is creating the user.

        Returns:
            CreateUserResponse: A response containing the created user's basic information.

        Raises:
            PhoneAlreadyExistsError: If the provided phone number already exists.
            EmailAlreadyExistsError: If the provided email address already exists.
        """
        # Check for existing user with same phone or email
        existing_user = await self.session.scalar(
            select(Users)
            .options(load_only(Users.phone, Users.email))
            .where(
                or_(
                    and_(Users.phone == phone, Users.phone.is_not(None)),
                    and_(Users.email == email, Users.email.is_not(None)),
                ),
                Users.deleted_at.is_(None),
            )
        )
        if existing_user:
            if phone and existing_user.phone == phone:
                raise PhoneAlreadyExistsError
            if email and existing_user.email == email:
                raise EmailAlreadyExistsError

        async with self.session.begin_nested():
            user = Users(
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email.lower(),
                created_by=user_id,
                updated_by=user_id,
            )
            self.session.add(user)

        async with self.session.begin_nested():
            await self.session.refresh(user)

        return CreateUserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def update_user(
        self,
        user_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        reason: str | None = None,
        current_user_id: str | None = None,
    ) -> UpdateUserResponse:
        """
        Updates a user with only basic information.

        Args:
            user_id (str): The ID of the user to update.
            first_name (str | None): The user's first name.
            last_name (str | None): The user's last name.
            phone (str | None): The user's phone number.
            email (str | None): The user's email address.
            current_user_id (str | None): The ID of the user who is updating.

        Returns:
            UpdateUserResponse: A response containing the updated user's information.

        Raises:
            UserNotFoundError: If no user with the provided ID is found.
            PhoneAlreadyExistsError: If the provided phone number already exists.
            EmailAlreadyExistsError: If the provided email address already exists.
        """
        # Get existing user
        user = await self.session.scalar(
            select(Users).where(and_(Users.id == user_id, Users.deleted_at.is_(None)))
        )
        if not user:
            raise UserNotFoundError

        # Check for existing user with same phone or email (excluding current user)
        if phone or email:
            existing_user = await self.session.scalar(
                select(Users)
                .options(load_only(Users.phone, Users.email))
                .where(
                    and_(
                        or_(
                            and_(Users.phone == phone, Users.phone.is_not(None)),
                            and_(Users.email == email, Users.email.is_not(None)),
                        ),
                        Users.id != user_id,
                        Users.deleted_at.is_(None),
                    )
                )
            )
            if existing_user:
                if phone and existing_user.phone == phone:
                    raise PhoneAlreadyExistsError
                if email and existing_user.email == email:
                    raise EmailAlreadyExistsError

        # Update fields
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone is not None:
            user.phone = phone
        if email is not None:
            user.email = email.lower()

        user.updated_by = current_user_id

        async with self.session.begin_nested():
            await self.session.commit()

        return UpdateUserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            updated_at=user.updated_at,
            message="User updated successfully",
        )

    async def assign_user_clients(
        self,
        user_id: str,
        assignments: list[UserClientAssignment],
        current_user_id: str | None = None,
    ) -> AssignUserClientsResponse:
        """
        Assigns clients and roles to a user by replacing all existing assignments with new ones.

        Args:
            user_id (str): The ID of the user to assign clients to.
            assignments (list[UserClientAssignment]): List of client assignments.
            current_user_id (str | None): The ID of the user who is making the assignment.

        Returns:
            AssignUserClientsResponse: A response containing the assignment results.

        Raises:
            UserNotFoundError: If no user with the provided ID is found.
            RoleNotFoundError: If any of the provided role IDs do not exist.
            ValueError: If duplicate client assignments are found.
        """
        # Check if user exists
        user = await self.session.scalar(
            select(Users).where(and_(Users.id == user_id, Users.deleted_at.is_(None)))
        )
        if not user:
            raise UserNotFoundError

        # Check for duplicate client assignments
        client_ids = [assignment.client_id for assignment in assignments]
        if len(client_ids) != len(set(client_ids)):
            raise UserDuplicateClientAssignmentError

        # Validate all roles exist before making any changes
        for assignment in assignments:
            # Check if role exists
            role = await self.session.scalar(
                select(Roles)
                .options(load_only(Roles.id))
                .where(and_(Roles.id == assignment.role_id, Roles.deleted_at.is_(None)))
            )
            if not role:
                raise RoleNotFoundError

        # Remove all existing assignments for this user
        existing_assignments = await self.session.scalars(
            select(UserRoleLink).where(
                and_(UserRoleLink.user_id == user_id, UserRoleLink.deleted_at.is_(None))
            )
        )
        existing_assignments = list(existing_assignments)

        for existing_assignment in existing_assignments:
            await self.session.delete(existing_assignment)

        # Create new assignments based on the payload
        assignment_results = []
        for assignment in assignments:
            new_assignment = UserRoleLink(
                user_id=user_id,
                client_id=assignment.client_id,
                role_id=assignment.role_id,
                created_by=current_user_id,
                updated_by=current_user_id,
            )
            self.session.add(new_assignment)

            assignment_results.append(
                UserClientAssignmentResponse(
                    client_id=assignment.client_id,
                    role_id=assignment.role_id,
                    status="assigned",
                )
            )

        async with self.session.begin_nested():
            await self.session.commit()

        return AssignUserClientsResponse(
            user_id=user_id,
            assignments=assignment_results,
            message="User client assignments completed successfully",
        )

    async def get_all_users(  # noqa: C901
        self,
        client_id: str,
        page_param: Params,
        user: str,
        user_ids: list[str] | None = None,
        search: str | None = None,
        role_slug: str | None = None,
        client_slug: str | None = None,
        sortby: UserSortBy | None = None,
        is_active: bool | None = None,
    ) -> Page[ListUserResponse]:
        """
        Retrieves a paginated list of users with optional filtering and sorting.

        Args:
          - client_id (str): The client id. This is required.
          - param (Params): Pagination parameters including page number and size.
          - user_ids (list[str] | None): Optional list of user IDs to filter.
          - search (str | None): Optional filter by email address or phone number.
          - role_slug (str | None): Optional filter by user role.
          - is_active (bool | None): Optional filter by active status.
          - sortby (UserSortBy | None): Optional sorting field and direction.

        Returns:
          - Page[ListUserResponse]: A response containing the paginated list of users.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.

        """
        query = (
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.email,
                    Users.phone,
                    Users.is_active,
                    Users.description,
                    Users.meta_data,
                    Users.first_name,
                    Users.last_name,
                    Users.created_at,
                    Users.updated_at,
                    Users.created_by,
                    Users.updated_by,
                ),
                selectinload(Users.role_links).selectinload(UserRoleLink.role),
                selectinload(Users.role_links).selectinload(UserRoleLink.client),
            )
            .where(Users.deleted_at.is_(None))
        )

        if user_ids:
            query = query.where(Users.id.in_(user_ids))

        if search:
            query = query.where(
                or_(
                    Users.email.ilike(f"%{search}%"),
                    Users.first_name.ilike(f"%{search}%"),
                    Users.last_name.ilike(f"%{search}%"),
                    Users.phone.ilike(f"%{search}%"),
                )
            )

        if role_slug:
            query = (
                query.join(UserRoleLink, Users.id == UserRoleLink.user_id)
                .join(Roles, UserRoleLink.role_id == Roles.id)
                .where(Roles.slug.ilike(f"%{role_slug}%"))
            )

        if client_slug:
            query = (
                query.join(UserRoleLink, Users.id == UserRoleLink.user_id)
                .join(Clients, UserRoleLink.client_id == Clients.id)
                .where(Clients.slug.ilike(f"%{client_slug}%"))
            )

        if is_active is not None:
            query = query.where(Users.is_active == is_active)

        if sortby in [UserSortBy.ROLE_DESC, UserSortBy.ROLE_ASC]:
            query = query.join(UserRoleLink, Users.id == UserRoleLink.user_id).join(
                Roles, UserRoleLink.role_id == Roles.id
            )

        sort_options = {
            UserSortBy.NAME_DESC: Users.first_name.desc(),
            UserSortBy.NAME_ASC: Users.first_name.asc(),
            UserSortBy.EMAIL_DESC: Users.email.desc(),
            UserSortBy.EMAIL_ASC: Users.email.asc(),
            UserSortBy.ROLE_DESC: Roles.name.desc(),
            UserSortBy.ROLE_ASC: Roles.name.asc(),
            UserSortBy.CREATED_AT_DESC: Users.created_at.desc(),
            UserSortBy.CREATED_AT_ASC: Users.created_at.asc(),
        }

        sort_order = sort_options.get(sortby, Users.created_at.desc())
        query = query.order_by(sort_order)

        pagination = await paginate(self.session, query, page_param)
        items = []

        for user in pagination.items:
            # Build assigns from role_links
            assigns = []
            if user.role_links:
                for role_link in user.role_links:
                    if role_link.role and role_link.client:
                        assigns.append(
                            UserAssignmentsResponse(
                                role=(
                                    RoleResponse(
                                        id=role_link.role.id, name=role_link.role.name
                                    )
                                    if role_link.role
                                    else None
                                ),
                                client=(
                                    ClientResponse(
                                        id=role_link.client.id,
                                        name=role_link.client.name,
                                    )
                                    if role_link.client
                                    else None
                                ),
                            )
                        )

            items.append(
                ListUserResponse(
                    id=user.id,
                    email=user.email,
                    phone=user.phone,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    assigns=assigns,
                    is_active=user.is_active,
                    description=user.description,
                    meta_data=user.meta_data,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    created_by=user.created_by,
                    updated_by=user.updated_by,
                )
            )

        pagination.items = items
        return pagination

    async def get_user_by_id(self, client_id: str, user_id: str) -> ListUserResponse:
        """
        Retrieves detailed information about a specific user by their ID.

        Args:
            - client_id (str): The client id. This is required.
            - user_id (str): The unique identifier of the user to retrieve.

        Returns:
            - ListUserResponse: A response containing the user's information.

        Raises:
            - UserNotFoundError: If no user with the provided username is found.

        """
        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.email,
                    Users.phone,
                    Users.is_active,
                    Users.description,
                    Users.meta_data,
                    Users.first_name,
                    Users.last_name,
                    Users.created_at,
                    Users.updated_at,
                    Users.created_by,
                    Users.updated_by,
                ),
                selectinload(Users.role_links).selectinload(UserRoleLink.role),
                selectinload(Users.role_links).selectinload(UserRoleLink.client),
            )
            .where(and_(Users.id == user_id, Users.deleted_at.is_(None)))
        )
        if not user:
            raise UserNotFoundError

        # Build assigns from role_links
        assigns = []
        if user.role_links:
            for role_link in user.role_links:
                if role_link.role and role_link.client:
                    assigns.append(
                        UserAssignmentsResponse(
                            role=(
                                RoleResponse(
                                    id=role_link.role.id, name=role_link.role.name
                                )
                                if role_link.role
                                else None
                            ),
                            client=(
                                ClientResponse(
                                    id=role_link.client.id, name=role_link.client.name
                                )
                                if role_link.client
                                else None
                            ),
                        )
                    )

        return ListUserResponse(
            id=user.id,
            email=user.email,
            phone=user.phone,
            first_name=user.first_name,
            last_name=user.last_name,
            assigns=assigns,
            is_active=user.is_active,
            description=user.description,
            meta_data=user.meta_data,
            created_at=user.created_at,
            updated_at=user.updated_at,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )

    async def change_user_status(
        self, user_id: str, current_user_id: str
    ) -> UserStatusResponse:
        """
        Toggles the active status of a user by their ID.

        Args:
          - user_id (str): The ID of the user whose status is to be changed.
          - current_user_id (str): The ID of the current user.
        Returns:
          - Users: A response indicating the user's updated status.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.

        """
        existing_user = await self.session.scalar(
            select(Users)
            .options(load_only(Users.id, Users.phone, Users.email, Users.is_active))
            .where(and_(Users.id == user_id, Users.deleted_at.is_(None)))
        )
        if not existing_user:
            raise UserNotFoundError

        if existing_user.is_active:
            existing_user.is_active = False
        else:
            existing_user.is_active = True

        existing_user.updated_by = current_user_id

        return UserStatusResponse(
            id=existing_user.id,
            is_active=existing_user.is_active,
            message="User status updated successfully",
        )

    async def _assign_user_roles(
        self, session: AsyncSession, user_id: str, role_ids: list[str], client_id: str
    ) -> None:
        """Synchronize user roles with the provided role_ids."""
        # Fetch current role links for the user
        existing_links = await session.scalars(
            select(UserRoleLink).where(
                UserRoleLink.user_id == user_id,
                UserRoleLink.client_id == client_id,
                UserRoleLink.deleted_at.is_(None),
            )
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
            link = UserRoleLink(user_id=user_id, role_id=role_id, client_id=client_id)
            session.add(link)

    async def update(  # noqa: C901
        self,
        client_id: str,
        user_id: str,
        email: EmailStr | None = None,
        phone: str | None = None,
        role_ids: list[str] | None = None,
        description: str | None = None,
        user_metadata: dict[str, Any] | None = None,
    ) -> UpdateUserResponse:
        """
        Updates the information of a specific user by their ID.

        Args:
            - client_id (str): The client id. This is required.
          - user_id (str): The unique identifier of the user to retrieve.
          - phone (str | None): The phone number of the user.
          - email (str | None): The email address of the user.
          - role_ids (list[str] | None) : List of role IDs to assign to the user.

          - description (str | None): The description of the user.

        Returns:
          - UpdateUserResponse: A response containing the updated user data.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.
          - PhoneAlreadyExistsError: If the provided phone number already exists.
          - EmailAlreadyExistsError: If the provided email address already exists.
          - RoleNotFoundError: If the provided role ID does not exist.


        """
        async with self.session.begin_nested():
            existing_user = await self.session.scalar(
                select(Users)
                .options(
                    load_only(
                        Users.id,
                        Users.phone,
                        Users.email,
                        Users.description,
                        Users.meta_data,
                        Users.first_name,
                        Users.last_name,
                        Users.is_active,
                    ),
                    selectinload(Users.roles),
                )
                .where(and_(Users.id == user_id, Users.deleted_at.is_(None)))
            )
            if not existing_user:
                raise UserNotFoundError

            if phone:
                existing_phone = await self.session.scalar(
                    select(Users.id).where(
                        and_(Users.phone == phone, Users.id != user_id)
                    )
                )
                if existing_phone:
                    raise PhoneAlreadyExistsError
            if email:
                existing_email = await self.session.scalar(
                    select(Users.id).where(
                        and_(Users.email == email, Users.id != user_id)
                    )
                )
                if existing_email:
                    raise EmailAlreadyExistsError
            if role_ids:
                roles_result = await self.session.scalars(
                    select(Roles)
                    .options(load_only(Roles.id, Roles.name))
                    .where(and_(Roles.id.in_(role_ids), Roles.deleted_at.is_(None)))
                )
                existing_roles = roles_result.all()
                if len(existing_roles) != len(role_ids):
                    raise RoleNotFoundError
                await self._assign_user_roles(
                    self.session, user_id, role_ids, client_id
                )

            existing_user.phone = phone if phone is not None else existing_user.phone
            existing_user.email = email if email is not None else existing_user.email
            existing_user.description = (
                description if description is not None else existing_user.description
            )
            existing_user.meta_data = (
                user_metadata if user_metadata is not None else existing_user.meta_data
            )

            return UpdateUserResponse(
                id=existing_user.id,
                first_name=existing_user.first_name,
                last_name=existing_user.last_name,
                email=existing_user.email,
                phone=existing_user.phone,
                is_active=existing_user.is_active,
                updated_at=existing_user.updated_at,
                message="User updated successfully",
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
            if (
                not module.parent_module_id
                or module.parent_module_id not in id_to_module
            ):
                roots.append(module)

        return [
            ModuleBasicResponse.model_validate(m, from_attributes=True) for m in roots
        ]

    async def get_self(self, client_id: str, user_id: str) -> UserSelfResponse:
        """
        Retrieves the profile information of the currently authenticated user,
        including only the role for the specific client they're logged into.

        Args:
        - client_id (str): The client id. This is required.
        - user_id (str): The user id. This is required.

        Returns:
        - UserResponse: A response containing the user's profile information with only the client-specific role.

        Raises:
        - UserNotFoundError: If no user with the provided user_id is found.
        """

        # Fetch the user information
        user = await self.session.scalar(select(Users).where(Users.id == user_id))
        if not user:
            raise UserNotFoundError

        # Fetch only the role for the specific client
        user_role_link = await self.session.scalar(
            select(UserRoleLink)
            .options(selectinload(UserRoleLink.role))
            .where(
                and_(
                    UserRoleLink.user_id == user_id,
                    UserRoleLink.client_id == client_id,
                    UserRoleLink.deleted_at.is_(None),
                )
            )
        )

        role_data = None
        if user_role_link and user_role_link.role:
            # Get role-specific module permission links for this client
            role_module_permission_links = await self.session.scalars(
                select(RoleModulePermissionLink).where(
                    and_(RoleModulePermissionLink.role_id == user_role_link.role.id)
                )
            )
            role_module_permission_links = list(role_module_permission_links)

            if role_module_permission_links:
                # Get all module IDs that have permissions for this role
                direct_module_ids = [
                    link.module_id for link in role_module_permission_links
                ]

                # First, fetch all modules that have direct permission links
                direct_modules_result = await self.session.scalars(
                    select(Modules)
                    .where(
                        Modules.id.in_(direct_module_ids), Modules.deleted_at.is_(None)
                    )
                    .options(
                        selectinload(Modules.permissions),
                        selectinload(Modules.child_modules),
                    )
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
                            Modules.id.in_(parent_module_ids),
                            Modules.deleted_at.is_(None),
                        )
                        .options(
                            selectinload(Modules.permissions),
                            selectinload(Modules.child_modules),
                        )
                    )
                    parent_modules = list(parent_modules_result)

                # Combine all modules (direct + parent)
                all_modules = direct_modules + parent_modules

                # Build the nested modules tree
                nested_modules = self.build_module_tree(
                    all_modules,
                    role_module_permission_links=role_module_permission_links,
                )

                role_data = UserSelfRoleResponse(
                    id=user_role_link.role.id,
                    name=user_role_link.role.name,
                    slug=user_role_link.role.slug,
                    modules=nested_modules,
                )
            else:
                role_data = UserSelfRoleResponse(
                    id=user_role_link.role.id,
                    name=user_role_link.role.name,
                    slug=user_role_link.role.slug,
                    modules=[],
                )

        # Return the full user profile, including only the client-specific role
        return UserSelfResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            role=role_data,
            is_active=user.is_active,
        )

    async def refresh_token(
        self, token: dict, refresh_token: str | None
    ) -> JSONResponse:
        """
        Refreshes the access token for an admin user.

        Args:
            token (dict): A dictionary containing user information, typically including the user ID.
            refresh_token (str | None): The refresh token to be included in the response, if any.

        Returns:
            JSONResponse: A response object containing the new access and refresh tokens,
                          along with a success status and HTTP 200 OK code.

        """

        refresh_token_key = Hash.make(refresh_token)
        cached_refresh_token = await redis.get(refresh_token_key)
        if not cached_refresh_token:
            raise UnauthorizedError(message=UNAUTHORIZED)

        if token:
            user_id = token.get("id")
            client_slug = token.get("client_id")
            user = await self.session.scalar(
                select(Users)
                .options(load_only(Users.id, Users.is_active))
                .where(Users.id == user_id)
            )

            if not user or not user.is_active:
                raise UnauthorizedError(message=UNAUTHORIZED)

            access_token = access.encode(
                payload={"id": str(user_id), "client_id": client_slug},
                expire_period=int(settings.ACCESS_TOKEN_EXP),
            )
            res = {"access_token": access_token, "refresh_token": refresh_token}
            data = {"status": SUCCESS, "code": status.HTTP_200_OK, "data": res}
            response = JSONResponse(content=data)

            hashed_user_id = Hash.make("uid:" + str(user_id) + ":" + client_slug)
            old_access_token = json.loads(cached_refresh_token).get("access_token")
            old_access_token_key = Hash.make(old_access_token)
            cached_access_token = await redis.get(old_access_token_key)
            if cached_access_token:
                await redis.delete(old_access_token_key)

            new_access_token_key = Hash.make(access_token)
            tokens_dumped_data = json.dumps(res)
            await redis.set(
                name=hashed_user_id,
                value=tokens_dumped_data,
                ex=settings.ACCESS_TOKEN_EXP,
            )
            await redis.set(
                name=new_access_token_key,
                value=tokens_dumped_data,
                ex=settings.ACCESS_TOKEN_EXP,
            )
            await redis.set(
                name=refresh_token_key,
                value=tokens_dumped_data,
                ex=settings.REFRESH_TOKEN_EXP,
            )

            return response

        raise InvalidJWTTokenException(INVALID_TOKEN)

    async def logout(self, access_token: str, request: Request) -> None:
        """
        Logout
        """
        key = Hash.make(access_token)
        exist_token = await redis.get(key)
        if not exist_token:
            raise UnauthorizedError(message=UNAUTHORIZED)

        token = access.decode(access_token)
        user_id = token.get("id")
        client_slug = token.get("client_id")

        user_obj = await self.session.scalar(
            select(Users).options(load_only(Users.id)).where(Users.id == user_id)
        )
        if not user_obj:
            raise UnauthorizedError(message=UNAUTHORIZED)

        hashed_user_id = Hash.make("uid:" + str(user_id) + ":" + client_slug)

        await redis.delete(hashed_user_id)

        refresh_token = json.loads(exist_token).get("refresh_token")

        await redis.delete(key)
        await redis.delete(Hash.make(refresh_token))
        await log_login_activity(
            self.session,
            LoginActivityCreate(
                user_id=user_id,
                client_id=client_slug,
                status=LoginActivityStatus.LOGOUT,
                activity="System Logout",
                reason="User logged out successfully",
                ip_address=request.client.host,
            ),
        )

    def _build_login_activity_query(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        status: Optional[str] = None,
        activity: Optional[str] = None,
    ):
        """
        Build login activity query.
        """
        filters = [
            LoginActivity.timestamp >= start_date,
            LoginActivity.timestamp <= end_date,
        ]

        if user_id:
            filters.append(LoginActivity.user_id == user_id)
        if client_id:
            filters.append(LoginActivity.client_id == client_id)
        if status:
            filters.append(LoginActivity.status == status)
        if activity:
            filters.append(LoginActivity.activity.ilike(f"%{activity}%"))

        return (
            select(LoginActivity)
            .options(
                selectinload(LoginActivity.user), selectinload(LoginActivity.client)
            )
            .where(and_(*filters))
            .order_by(LoginActivity.timestamp.desc())
        )

    async def get_all_login_activities(
        self,
        page_param: Params,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        status: Optional[str] = None,
        activity: Optional[str] = None,
    ) -> Page[LoginActivityOut]:
        """
        Get all login activities.
        """
        query = self._build_login_activity_query(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            client_id=client_id,
            status=status,
            activity=activity,
        )

        raw_page: AbstractPage = await paginate(self.session, query, params=page_param)

        # Convert ORM -> Pydantic
        return Page[LoginActivityOut].construct(
            items=[LoginActivityOut.model_validate(item) for item in raw_page.items],
            total=raw_page.total,
            page=raw_page.page,
            size=raw_page.size,
            pages=raw_page.pages,
        )

    def generate_login_activity_pdf(self, activities: list) -> bytes:
        """
        Generate login activity PDF.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
        )
        story = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], alignment=1)

        wrap_style = ParagraphStyle(
            name="WrapStyle", fontSize=9, leading=11, wordWrap="LTR"
        )

        story.append(Paragraph("Login Activity Report", title_style))
        story.append(Spacer(1, 12))

        data = [
            [
                "Sr.",
                "User Name",
                "Client Name",
                "IP Address",
                "Action",
                "Reason",
                "Activity",
            ]
        ]

        for idx, entry in enumerate(activities, start=1):
            data.append(
                [
                    str(idx),
                    Paragraph(
                        (
                            f"{entry.user.first_name} {entry.user.last_name}"
                            if entry.user
                            else "N/A"
                        ),
                        wrap_style,
                    ),
                    Paragraph(entry.client.name if entry.client else "N/A", wrap_style),
                    Paragraph(entry.ip_address or "N/A", wrap_style),
                    Paragraph(entry.status, wrap_style),
                    Paragraph(entry.reason or "N/A", wrap_style),
                    Paragraph(entry.activity, wrap_style),
                ]
            )

        col_widths = [
            0.5 * inch,
            1.8 * inch,
            1.8 * inch,
            1.4 * inch,
            1.2 * inch,
            2.8 * inch,
            2.0 * inch,
        ]

        table = Table(data, colWidths=col_widths)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.whitesmoke, colors.white],
                    ),
                ]
            )
        )

        story.append(table)
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    async def export_login_activities(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        status: Optional[str] = None,
        activity: Optional[str] = None,
    ) -> StreamingResponse:
        """
        Export login activities as PDF.
        """
        query = self._build_login_activity_query(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            client_id=client_id,
            status=status,
            activity=activity,
        )
        result = await self.session.execute(query)
        records = result.scalars().all()

        pdf_data = self.generate_login_activity_pdf(records)
        return StreamingResponse(
            BytesIO(pdf_data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=login_activities.pdf"
            },
        )
