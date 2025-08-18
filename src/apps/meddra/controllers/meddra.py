from typing import Annotated

from fastapi import APIRouter, Depends, status

from apps.meddra.schemas.request import (
    MeddraDetailSearchRequest,
    MeddraListSearchRequest,
)
from apps.meddra.schemas.response import MeddraDetailNode, MeddraTerm, MeddraVersion
from apps.meddra.services.meddra import MeddraService
from core.external_service_client.aicloudbase.client import AICBClient
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/meddra", tags=["meddra"])


@router.post(
    "/version-list",
    status_code=status.HTTP_200_OK,
    summary="Get MedDRA versions from AiCloudBase",
)
async def meddra_version_list(
    service: Annotated[MeddraService, Depends()], aicb: Annotated[AICBClient, Depends()]
) -> BaseResponse[list[MeddraVersion]]:
    """
    Get MedDRA versions from AiCloudBase.
    """
    return BaseResponse(data=await service.get_meddra_versions(aicb))


@router.post(
    "/term-search",
    status_code=status.HTTP_200_OK,
    summary="Search MedDRA terms from AiCloudBase",
)
async def meddra_term_search(
    req: MeddraListSearchRequest,
    service: Annotated[MeddraService, Depends()],
    aicb: Annotated[AICBClient, Depends()],
) -> BaseResponse[list[MeddraTerm]]:
    """
    Search for MedDRA terms in AiCloudBase.
    """
    return BaseResponse(data=await service.search_meddra_terms(aicb, req))


@router.post(
    "/detail-search",
    status_code=status.HTTP_200_OK,
    summary="MedDRA hierarchical detail for a specific code",
)
async def meddra_detail_search(
    req: MeddraDetailSearchRequest,
    service: Annotated[MeddraService, Depends()],
    aicb: Annotated[AICBClient, Depends()],
) -> BaseResponse[list[MeddraDetailNode]]:
    """
    Search for MedDRA detail in AiCloudBase.
    """
    return BaseResponse(data=await service.search_meddra_detail(aicb, req))
