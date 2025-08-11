import json
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

import constants
from apps.admin.schemas.admin_user_response import AdminListUsersResponse
from apps.user.exceptions import (
    InvalidCredentialsException,
    InvalidRequestException,
    UserNotFoundException,
    WeakPasswordException,
)
from apps.user.models.user import UserModel
from config import settings
from core.common_helpers import create_tokens, decrypt, validate_email
from core.db import db_session
from core.exceptions import BadRequestError
from core.types import RoleType
from core.utils import strong_password
from core.utils.hashing import hash_password, verify_password
from core.utils.pagination import PaginatedResponse, PaginationParams, paginate_query


class AdminUserService:
    """
    Service providing methods for managing admin-related user operations.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initializes the AdminUserService with an asynchronous database session.
        This method also calls a database connection which is injected here.

        :param session: an asynchronous database connection
        """
        self.session = session

    async def login_admin(
        self, request: Request, encrypted_data: str, encrypted_key: str, iv: str
    ) -> dict[str, str]:
        """
        Log in an admin and generate authentication tokens.

        Args:
            request(Request):  The incoming request object.
            encrypted_data (str): The encrypted data containing the login credentials.
            encrypted_key (str): The encrypted key used to encrypt the data.
            iv (str): The initialization vector used to encrypt the data.

        Returns:
            dict[str, str]: A dictionary containing the authentication tokens.

        Raises:
            InvalidCredentialsException: If the login credentials are invalid.
        """
        decrypted_data = await decrypt(
            rsa_key=request.app.state.rsa_key,
            enc_data=encrypted_data,
            encrypt_key=encrypted_key,
            iv_input=iv,
            time_check=settings.DECRYPT_REQUEST_TIME_CHECK or False,
            timeout=constants.PAYLOAD_TIMEOUT,
        )
        decrypted_data = json.loads(decrypted_data)

        email = decrypted_data.get("email")
        password = decrypted_data.get("password")

        if email is None:
            raise BadRequestError(message=constants.EMAIL_FIELD_REQUIRED)

        if password is None:
            raise BadRequestError(message=constants.PASSWORD_FIELD_REQUIRED)

        validate_email(email=email)

        user = await self.session.scalar(
            select(UserModel).where(
                and_(UserModel.email == email, UserModel.role == RoleType.ADMIN)
            )
        )
        if not user:
            raise InvalidCredentialsException
        verify = await verify_password(
            hashed_password=user.password, plain_password=password
        )
        if not verify:
            raise InvalidCredentialsException

        return await create_tokens(user_id=user.id, role=user.role)

    async def get_users(self, params: Params) -> Page[UserModel]:
        """
        Retrieve a paginated list of users.

        Args:
            params (Params): Pagination parameters to control the page size and number.

        Returns:
            Page[UserModel]: A paginated list of UserModel instances.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found.
        """
        query = select(UserModel).options(
            load_only(
                UserModel.first_name,
                UserModel.last_name,
                UserModel.email,
                UserModel.phone,
                UserModel.created_by,
                UserModel.updated_by,
                UserModel.deleted_by,
            )
        )

        return await paginate(self.session, query, params)

    async def get_self_admin(self, user_id: UUID) -> UserModel:
        """
        Retrieve user information by user ID.

        Args:
            user_id (UUID): The ID of the user.

        Returns:
            UserModel: The user model with the user's information.
        """
        return await self.session.scalar(
            select(UserModel)
            .options(
                load_only(
                    UserModel.id,
                    UserModel.email,
                    UserModel.first_name,
                    UserModel.last_name,
                )
            )
            .where(UserModel.id == user_id)
        )

    async def change_password(
        self,
        request: Request,
        user: UUID,
        encrypted_data: str,
        encrypted_key: str,
        iv: str,
    ):
        """
        Change the password for a user.

        Args:
            user (UUID): The ID of the user.
            encrypted_data (str): The encrypted data containing the current and new passwords.
            encrypted_key (str): The encrypted key used to encrypt the data.
            iv (str): The initialization vector used to encrypt the data.

        Returns:
            UserModel: The updated user model with the new password.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found.
            InvalidCredentialsException: If the current password is incorrect.
        """

        decrypted_data = await decrypt(
            rsa_key=request.app.state.rsa_key,
            enc_data=encrypted_data,
            encrypt_key=encrypted_key,
            iv_input=iv,
        )
        decrypted_data = json.loads(decrypted_data)

        current_password = decrypted_data.get("current_password")
        new_password = decrypted_data.get("new_password")

        if not current_password or not new_password:
            raise InvalidRequestException

        if not strong_password(new_password):
            raise WeakPasswordException

        current_user = await self.session.scalar(
            select(UserModel).where(UserModel.id == user)
        )

        if not current_user:
            raise UserNotFoundException

        verify = await verify_password(
            hashed_password=current_user.password, plain_password=current_password
        )

        if not verify:
            raise InvalidCredentialsException

        current_user.password = await hash_password(new_password)

        return current_user

    async def get_users_advanced(
        self, params: PaginationParams
    ) -> PaginatedResponse[AdminListUsersResponse]:
        """
        Retrieve a paginated list of users with advanced features.

        This method provides advanced pagination with search, filtering, sorting,
        and date range capabilities.

        Args:
            params (PaginationParams): Advanced pagination parameters including search, filters, and sorting.

        Returns:
            PaginatedResponse[AdminListUsersResponse]: Enhanced paginated response with metadata.
        """
        # Base query with all necessary fields
        base_query = select(UserModel).options(
            load_only(
                UserModel.id,
                UserModel.first_name,
                UserModel.last_name,
                UserModel.email,
                UserModel.phone,
                UserModel.role,
                UserModel.created_at,
                UserModel.updated_at,
                UserModel.created_by,
                UserModel.updated_by,
                UserModel.deleted_by,
                UserModel.deleted_at,
            )
        )

        # Use the advanced pagination utility
        paginated_result = await paginate_query(
            query=base_query,
            session=self.session,
            params=params,
            search_fields=["first_name", "last_name", "email", "phone"],
            allowed_filters=["role", "created_by", "updated_by"],
            allowed_sort_fields=[
                "first_name",
                "last_name",
                "email",
                "created_at",
                "updated_at",
            ],
            date_field="created_at",
        )

        # Convert UserModel instances to AdminListUsersResponse
        admin_users = []
        for user in paginated_result.items:
            # Get user names for created_by, updated_by, deleted_by
            created_by_user = None
            updated_by_user = None
            deleted_by_user = None

            created_by_user_name = ""
            updated_by_user_name = ""
            deleted_by_user_name = ""

            if user.created_by:
                created_by_user = await self.session.scalar(
                    select(UserModel)
                    .options(load_only(UserModel.first_name, UserModel.last_name))
                    .where(UserModel.id == user.created_by)
                )
                if created_by_user:
                    created_by_user_name = (
                        f"{created_by_user.first_name} {created_by_user.last_name}"
                    )

            if user.updated_by:
                updated_by_user = await self.session.scalar(
                    select(UserModel)
                    .options(load_only(UserModel.first_name, UserModel.last_name))
                    .where(UserModel.id == user.updated_by)
                )
                if updated_by_user:
                    updated_by_user_name = (
                        f"{updated_by_user.first_name} {updated_by_user.last_name}"
                    )

            if user.deleted_by:
                deleted_by_user = await self.session.scalar(
                    select(UserModel)
                    .options(load_only(UserModel.first_name, UserModel.last_name))
                    .where(UserModel.id == user.deleted_by)
                )
                if deleted_by_user:
                    deleted_by_user_name = (
                        f"{deleted_by_user.first_name} {deleted_by_user.last_name}"
                    )

            admin_user = AdminListUsersResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=user.phone or "",
                created_by_user_name=created_by_user_name,
                updated_by_user_name=updated_by_user_name,
                deleted_by_user_name=deleted_by_user_name,
            )
            admin_users.append(admin_user)

        # Create new paginated response with converted data
        return PaginatedResponse.create(
            items=admin_users, total=paginated_result.total, params=params
        )
