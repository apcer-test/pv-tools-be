from typing import Annotated, Any

from fastapi import Path
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.clients.models.clients import Clients
from apps.users.models import Users
from core.auth import access
from core.constants import ErrorMessage
from core.db import db_session
from core.dependencies import (
    verify_access_token
)
from core.dependencies.auth import access_jwt
from core.exceptions import UnauthorizedError
from core.utils.resolve_context_ids import get_context_ids_from_keys


async def get_user_id_from_access_token(
    token_claims: Annotated[dict[str, Any], Depends(verify_access_token)],
) -> int:
    """Fetch the user ID from the token claims.

    :param token_claims: The token payload.
    :return: The user ID.
    """
    user_id = token_claims.get("sub")
    if not user_id:
        raise UnauthorizedError(message=ErrorMessage.UNAUTHORIZED)

    return int(user_id)


async def current_user(
    token_claims: Annotated[dict[str, Any], Depends(access)],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> Users:
    """Fetch the client user and return it.

    :param token_claims: The token payload.
    :param session: The database session.
    :param client_id (int): the client's id

    :return: The user object.
    """

    user = await session.scalar(
        select(Users).where(
             Users.id == token_claims.get("id"), Users.clients.any(Clients.id == token_claims.get("client_id"))
        )
    )
    if not user:
        raise UnauthorizedError(message=ErrorMessage.UNAUTHORIZED)

    return {"user": user, "client_id": token_claims.get("client_id")}