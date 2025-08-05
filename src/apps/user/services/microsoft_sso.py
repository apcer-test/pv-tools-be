from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from apps.user.exceptions import EmailNotFoundError, UserNotFoundException
from apps.user.models.user import UserModel
from core.common_helpers import create_tokens
from core.db import db_session
from src.config import settings


class MicrosoftSSOService:
    """Service to handle Microsoft SSO authentication using Authlib"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize MicrosoftSSOService with database session

        Args:
            session: Database session for user operations
        """
        self.session = session

    async def sso_user(self, token: str, **kwargs) -> dict[str, str]:
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
                select(UserModel).where(UserModel.email == email)
            )

            if not user:
                raise UserNotFoundException

            res = await create_tokens(user_id=user.id, role=user.role)

            redirect_link = (
                f"{settings.LOGIN_REDIRECT_URL}?access-token={res.get('access_token')}&refresh-token="
                f"{res.get('refresh_token')}"
            )

            return RedirectResponse(url=redirect_link)
        except Exception as e:
            raise e
