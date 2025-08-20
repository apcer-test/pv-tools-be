import json
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.meddra.schemas.request import (
    MeddraDetailSearchRequest,
    MeddraListSearchRequest,
)
from apps.meddra.schemas.response import MeddraDetailNode, MeddraTerm, MeddraVersion
from config import settings
from core.db import db_session, redis
from core.external_service_client.aicloudbase.client import AICBClient
from core.utils.redis_key_utils import RedisKeyConfig
from core.constants import RedisTTL


class MeddraService:
    """
    Service with methods to handle meddra authentication and information.

    This service provides methods for creating meddra, logging in, and retrieving meddra information.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize meddraService with a database session
        This method also calls a database connection which is injected here.

        Args:
            session (AsyncSession): An asynchronous database connection.
        """
        self.session = session
        self.redis = redis

    # create your services here
    async def get_meddra_versions(self, aicb: AICBClient) -> list[MeddraVersion]:
        """
        Fetch MedDRA version list from AiCloudBase and normalize the response
        to match the required shape.
        """
        key = RedisKeyConfig.get_aicb_meddra_version_list_key()

        # 1) Try cache
        cached = await self.redis.get(key)
        if cached:
            items = json.loads(cached)
            return [MeddraVersion(**it) for it in items]

        # 2) Fallback → external call
        versions: list[MeddraVersion] = await aicb.meddra_version_list(
            username=settings.AICB_USERNAME, password=settings.AICB_PASSWORD
        )

        # 3) Store in cache (TTL = 3600s)
        payload = [v.model_dump() for v in versions]
        await self.redis.set(
            key, json.dumps(payload), ex=RedisTTL.AICB_MEDDRA_VERSION_LIST.value
        )

        return versions

    async def search_meddra_terms(
        self, aicb: AICBClient, req: MeddraListSearchRequest
    ) -> list[MeddraTerm]:
        """
        Search for MedDRA terms in AiCloudBase.
        """
        return await aicb.meddra_list_search(
            version_id=req.version_id,
            level=req.level,
            levelcode=req.levelcode,
            term=req.term,
            condition=req.condition,
            orderby=req.orderby,
            soctype=req.soctype,
            matchcase=req.matchcase,
            username=settings.AICB_USERNAME,
            password=settings.AICB_PASSWORD,
        )

    async def search_meddra_detail(
        self, aicb: AICBClient, req: MeddraDetailSearchRequest
    ) -> list[MeddraDetailNode]:
        """
        Search for MedDRA detail in AiCloudBase.
        """
        return await aicb.meddra_detail_search(
            level=req.level,
            levelcode=req.levelcode,
            version_id=req.version_id,
            soctype=req.soctype or "Y",
            username=settings.AICB_USERNAME,
            password=settings.AICB_PASSWORD,
        )
