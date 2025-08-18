"""Services for Users."""

from collections import defaultdict
import copy
from datetime import datetime, UTC
from typing import Annotated, Any

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import EmailStr
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from apps.clients.models.clients import Clients
from apps.modules.models.modules import Modules
from apps.modules.schemas.response import ModuleResponse
from apps.roles.execeptions import RoleNotFoundError
from apps.roles.models import Roles
from apps.roles.models.roles import RoleModulePermissionLink
from apps.roles.schemas.response import ModuleBasicResponse
from apps.roles.services import RoleService
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
from apps.users.schemas.request import AssignUserClientsRequest, UserClientAssignment
from apps.users.schemas.response import (
    ClientResponse,
    CreateUserResponse,
    ListUserResponse,
    RoleResponse,
    UpdateUserResponse,
    UserAssignmentsResponse,
    UserResponse,
    UserSelfResponse,
    UserSelfRoleResponse,
    UserStatusResponse,
    AssignUserClientsResponse,
    UserClientAssignmentResponse,
)
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from apps.users.exceptions import EmailNotFoundError, UserNotFoundException
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
                select(Users)
                .options(
                    selectinload(Users.roles)
                )
                .join(UserRoleLink, Users.id == UserRoleLink.user_id)
                .where(
                    and_(
                        Users.email == email,
                        Users.deleted_at.is_(None),
                        UserRoleLink.client_id == client_slug
                    )
                )
            )

            if not user:
                raise UserNotFoundException

            res = await create_tokens(user_id=user.id, client_slug=client_slug)

            redirect_link = (
                f"{settings.LOGIN_REDIRECT_URL}?accessToken={res.get('access_token')}&refreshToken="
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
    ) -> None:
        self.session = session
        self.role_service = role_service

    async def create_user(
        self,
        client_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        role_ids: list[str] | None = None,
        description: str | None = None,
        user_metadata: dict | None = None,
        user_id: str | None = None,
    ) -> CreateUserResponse:
        """
        Creates a new user with the provided information.

         Args:
          - client_id (str): The client id. This is required.
          - phone (str | None): The phone number of the user.
          - email (str | None): The email address of the user.
          - role_ids (list[str] | None) : List of role IDs to assign to the user.

          - description (str | None): The description of the user.
          - meta_data (dict[str, Any] | None): The metadata of the user.
          - user_id (str | None): The ID of the user who is creating the user.
        Returns:
          - CreateUserResponse: A response containing the created user's basic information.

        Raises:
          - PhoneAlreadyExistsError: If the provided phone number already exists.
          - EmailAlreadyExistsError: If the provided email address already exists.
          - RoleNotFoundError: If any of the provided role IDs do not exist.

        """

        if role_ids is None:
            role_ids = []
        
        existing_user = await self.session.scalar(
            select(Users)
            .options(load_only(Users.phone, Users.email))
            .where(
                or_(
                    and_(Users.phone == phone, Users.phone.is_not(None)),
                    and_(Users.email == email, Users.email.is_not(None)),
                ),
                Users.deleted_at.is_(None)
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
                        Roles.client_id == client_id,
                        Roles.id.in_(role_ids),
                        Roles.deleted_at.is_(None),
                    )
                )
            )
            existing_roles = list(existing_roles_result)
            if len(existing_roles) != len(role_ids):
                raise RoleNotFoundError

        async with self.session.begin_nested():
            user = Users(
                first_name=first_name or "Unknown",
                last_name=last_name or "Unknown",
                phone=phone,
                email=email,
                description=description,
                meta_data=user_metadata,
                created_by=user_id,
                updated_by=user_id,
            )
            self.session.add(user)

        async with self.session.begin_nested():
            await self.session.refresh(user)

        async with self.session.begin_nested():
            for role_id in role_ids:
                user_role_link = UserRoleLink(
                    user_id=user.id,
                    role_id=role_id,
                    client_id=client_id,
                )
                self.session.add(user_role_link)

        return CreateUserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            reporting_manager_id=user.reporting_manager_id,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def create_simple_user(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        reporting_manager_id: str | None = None,
        user_id: str | None = None,
    ) -> CreateUserResponse:
        """
        Creates a new user with only basic information.

        Args:
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            phone (str): The user's phone number.
            email (str): The user's email address.
            reporting_manager_id (str | None): The user's reporting manager ID.
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
                Users.deleted_at.is_(None)
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
                reporting_manager_id=reporting_manager_id,
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
            reporting_manager_id=user.reporting_manager_id,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def update_simple_user(
        self,
        user_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        reporting_manager_id: str | None = None,
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
            reporting_manager_id (str | None): The user's reporting manager ID.
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
            select(Users)
            .where(
                and_(
                    Users.id == user_id,
                    Users.deleted_at.is_(None)
                )
            )
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
                        Users.deleted_at.is_(None)
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
        if reporting_manager_id is not None:
            user.reporting_manager_id = reporting_manager_id

        user.updated_by = current_user_id

        async with self.session.begin_nested():
            await self.session.commit()

        return UpdateUserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            reporting_manager_id=user.reporting_manager_id,
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
        Assigns clients, roles, and user types to a user.

        Args:
            user_id (str): The ID of the user to assign clients to.
            assignments (list[UserClientAssignment]): List of client assignments.
            current_user_id (str | None): The ID of the user who is making the assignment.

        Returns:
            AssignUserClientsResponse: A response containing the assignment results.

        Raises:
            UserNotFoundError: If no user with the provided ID is found.
            RoleNotFoundError: If any of the provided role IDs do not exist.
        """
        # Check if user exists
        user = await self.session.scalar(
            select(Users)
            .where(
                and_(
                    Users.id == user_id,
                    Users.deleted_at.is_(None)
                )
            )
        )
        if not user:
            raise UserNotFoundError

        assignment_results = []

        for assignment in assignments:
            # Check if role exists
            role = await self.session.scalar(
                select(Roles)
                .options(load_only(Roles.id))
                .where(
                    and_(
                        Roles.id == assignment.role_id,
                        Roles.deleted_at.is_(None)
                    )
                )
            )
            if not role:
                raise RoleNotFoundError

            # Check if assignment already exists
            existing_assignment = await self.session.scalar(
                select(UserRoleLink)
                .where(
                    and_(
                        UserRoleLink.user_id == user_id,
                        UserRoleLink.client_id == assignment.client_id,
                        UserRoleLink.role_id == assignment.role_id,
                        UserRoleLink.deleted_at.is_(None)
                    )
                )
            )

            if existing_assignment:
                # Update existing assignment
                existing_assignment.updated_by = current_user_id
                status = "updated"
            else:
                # Create new assignment
                new_assignment = UserRoleLink(
                    user_id=user_id,
                    client_id=assignment.client_id,
                    role_id=assignment.role_id,
                    created_by=current_user_id,
                    updated_by=current_user_id,
                )
                self.session.add(new_assignment)
                status = "assigned"

            assignment_results.append(
                UserClientAssignmentResponse(
                    client_id=assignment.client_id,
                    role_id=assignment.role_id,
                    status=status,
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
            query = query.join(UserRoleLink, Users.id == UserRoleLink.user_id).join(Roles, UserRoleLink.role_id == Roles.id).where(Roles.slug.ilike(f"%{role_slug}%"))

        if client_slug:
            query = query.join(UserRoleLink, Users.id == UserRoleLink.user_id).join(Clients, UserRoleLink.client_id == Clients.id).where(Clients.slug.ilike(f"%{client_slug}%"))

        if is_active is not None:
            query = query.where(Users.is_active == is_active)

        if sortby in [UserSortBy.ROLE_DESC, UserSortBy.ROLE_ASC]:
            query = query.join(UserRoleLink, Users.id == UserRoleLink.user_id).join(Roles, UserRoleLink.role_id == Roles.id)

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
                        assigns.append(UserAssignmentsResponse(
                            role=RoleResponse(id=role_link.role.id, name=role_link.role.name) if role_link.role else None,
                            client=ClientResponse(id=role_link.client.id, name=role_link.client.name) if role_link.client else None
                        ))
            
            items.append(ListUserResponse(
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
            ))
        
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
            .where(
                and_(
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not user:
            raise UserNotFoundError
        
        # Build assigns from role_links
        assigns = []
        if user.role_links:
            for role_link in user.role_links:
                if role_link.role and role_link.client:
                    assigns.append(UserAssignmentsResponse(
                        role=RoleResponse(id=role_link.role.id, name=role_link.role.name) if role_link.role else None,
                        client=ClientResponse(id=role_link.client.id, name=role_link.client.name) if role_link.client else None
                    ))
        
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

    async def change_user_status(self, user_id: str, current_user_id: str) -> UserStatusResponse:
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
            .options(
                load_only(
                    Users.id,
                    Users.phone,
                    Users.email,
                    Users.is_active,
                )
            )
            .where(
                and_(
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
            select(UserRoleLink).where(UserRoleLink.user_id == user_id, UserRoleLink.client_id == client_id, UserRoleLink.deleted_at.is_(None))
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
                client_id=client_id,
            )
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
                .where(
                    and_(
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
                            Roles.client_id == client_id,
                            Roles.id.in_(role_ids),
                            Roles.deleted_at.is_(None),
                        )
                    )
                )
                existing_roles = roles_result.all()
                if len(existing_roles) != len(role_ids):
                    raise RoleNotFoundError
                await self._assign_user_roles(self.session, user_id, role_ids, client_id)
                roles = existing_roles



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
            if not module.parent_module_id or module.parent_module_id not in id_to_module:
                roots.append(module)

        return [ModuleBasicResponse.model_validate(m, from_attributes=True) for m in roots]


    async def get_self(self, client_id: str, user_id: str) -> UserSelfResponse:
        """
        Retrieves the profile information of the currently authenticated user, 
        including roles, modules, child modules, and permissions.

        Args:
        - client_id (str): The client id. This is required.
        - user_id (str): The user id. This is required.

        Returns:
        - UserResponse: A response containing the user's profile information with roles, modules, child modules, and permissions.

        Raises:
        - UserNotFoundError: If no user with the provided user_id is found.

        """

        # Fetch the user information along with related user types and roles
        user = await self.session.scalar(
            select(Users)
            .options(
                selectinload(Users.roles),
            )
            .where(
                Users.id == user_id,
            )
        )
        if not user:
            raise UserNotFoundError

        # Fetch role-specific module permission links
        role_module_permission_links = await self.session.scalars(
            select(RoleModulePermissionLink)
            .where(
                RoleModulePermissionLink.role_id.in_([role.id for role in user.roles]),
                RoleModulePermissionLink.client_id == client_id,
            )
        )
        role_module_permission_links = role_module_permission_links.unique().all()

        # Build the module tree for each role
        role_data = []
        for role in user.roles:
            # Get the list of module ids for the role
            role_module_links = [
                link for link in role_module_permission_links if link.role_id == role.id
            ]
            if role_module_links:
                # Get all module IDs that have permissions for this role
                direct_module_ids = [link.module_id for link in role_module_links]
                
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
                
                # Build the nested modules tree
                nested_modules = self.build_module_tree(all_modules, role_module_permission_links=role_module_links)

                role_data.append(
                    UserSelfRoleResponse(
                        id=role.id,
                        name=role.name,
                        slug=role.slug,
                        description=role.description,
                        role_metadata=role.meta_data,
                        modules=nested_modules,  # Add modules with child modules and permissions
                    )
                )
            else:
                role_data.append(
                    UserSelfRoleResponse(
                        id=role.id,
                        name=role.name,
                        slug=role.slug,
                        description=role.description,
                        role_metadata=role.meta_data,
                        modules=[],
                    )
                )

        # Return the full user profile, including roles, modules, and other details
        return UserSelfResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            description=user.description,
            user_metadata=user.meta_data,
            roles=role_data,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
            reporting_manager_id=user.reporting_manager_id,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
