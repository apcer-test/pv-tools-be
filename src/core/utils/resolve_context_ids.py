from typing import Annotated

from fastapi import Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.clients.models.clients import Clients
from apps.clients.exceptions import ClientNotFoundError
from core.db import db_session


async def get_context_ids_from_keys(
    session: AsyncSession,
    client_id: str,
) -> int | None:
    client_id = None
    if client_id is not None:
        client_query = Clients.id == client_id

        client_id = await session.scalar(
            select(Clients.id).where(and_(client_query, Clients.deleted_at.is_(None)))
        )
        if not client_id:
            raise ClientNotFoundError

    return client_id


async def resolve_context_ids(
    session: Annotated[AsyncSession, Depends(db_session)],
    client_slug: str,
) -> int | None:
    return await get_context_ids_from_keys(
        session=session, client_slug=client_slug
    )
