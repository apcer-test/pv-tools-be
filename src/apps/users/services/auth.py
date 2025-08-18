from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.exceptions import InvalidCredentialsError, UserNotFoundError
from apps.users.models import TenantUsersModel
from apps.users.schemas.response import LoginResponse
from core.common_helpers import create_tokens
from core.db import db_session
from core.utils.hashing import verify_password


class AuthService:
    """Service with methods to set and get values."""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Call method to inject db_session as a dependency.

        This method also calls a database connection which is injected here.

        :param session: an asynchronous database connection
        """
        self.session = session

    async def login(self, user_name: str, password: str) -> LoginResponse:
        """Authenticate a user by checking the provided username and password.

        Args:
        - user_name (str): The user_name of the user trying to log in.
        - password (str): The password provided by the user.
        - kwargs (dict): Additional keyword arguments.

        Returns:
        - LoginResponse:
            - LoginResponse: Contains access and refresh tokens and user information.

        Raises:
        - UserNotFoundError: If no user with the provided username is found.
        - UserLoginLocked: If the user's account is locked due to too many failed
        login attempts.
        """
        user_query = select(TenantUsersModel).where(
            TenantUsersModel.user_name.ilike(user_name)
        )

        user = await self.session.scalar(user_query)
        if not user:
            raise UserNotFoundError

        verify = verify_password(hashed_password=user.password, plain_password=password)
        if not verify:
            raise InvalidCredentialsError
        tokens = await create_tokens(user_id=user.id)
        tokens["user_name"] = user.user_name
        tokens["user_id"] = user.id
        return tokens
