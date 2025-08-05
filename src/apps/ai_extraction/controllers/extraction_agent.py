"""Extraction Agent Controller - API endpoints for managing extraction agents"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status
from ulid import ULID

from apps.ai_extraction.schemas.request import ExtractionAgentCreateRequest
from apps.ai_extraction.services.extraction_agent import ExtractionAgentService
from core.utils.schema import BaseResponse, SuccessResponse

router = APIRouter(prefix="/extraction-agents", tags=["Extraction Agents"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create a new extraction agent",
    description="Create a new extraction agent",
    operation_id="create_extraction_agent",
)
async def create_agent(
    body: Annotated[ExtractionAgentCreateRequest, Body()],
    service: Annotated[ExtractionAgentService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """Create a new extraction agent."""
    return BaseResponse(data=await service.create_agent(body))


@router.put(
    "/{agent_id}",
    status_code=status.HTTP_200_OK,
    name="Update an existing extraction agent",
    description="Update an existing extraction agent",
    operation_id="update_extraction_agent",
)
async def update_agent(
    agent_id: Annotated[ULID, Path(description="ID of the agent to update")],
    body: Annotated[ExtractionAgentCreateRequest, Body()],
    service: Annotated[ExtractionAgentService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """Update an existing extraction agent."""
    return BaseResponse(data=await service.update_agent(agent_id, **body.model_dump()))
