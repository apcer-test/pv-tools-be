from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from ulid import ULID

from apps.ai_extraction.schemas.request import PromptTemplateCreateRequest
from apps.ai_extraction.schemas.response import PromptTemplateResponse
from apps.ai_extraction.services.prompt_registry import PromptRegistry
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/api/prompt-templates", tags=["Prompt Templates"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Prompt Template",
    description="Create a new prompt template",
    operation_id="create_prompt_template",
)
async def create_prompt_template(
    template_data: PromptTemplateCreateRequest,
    service: Annotated[PromptRegistry, Depends()],
) -> BaseResponse[PromptTemplateResponse]:
    """
    Create a new prompt template.

    Args:
        template_data: The template data to create

    Returns:
        The created template with its ID

    Raises:
        HTTPException: If document type doesn't exist or validation fails
    """
    try:
        template = await service.create_template(template_data)
        return BaseResponse(data=template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt template: {str(e)}",
        )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Prompt Templates",
    description="Get all prompt templates",
    operation_id="get_prompt_templates",
)
async def get_prompt_templates(
    service: Annotated[PromptRegistry, Depends()],
    search: Optional[str] = Query(None, description="Search by document type ID"),
) -> BaseResponse[list[PromptTemplateResponse]]:
    """
    Get all prompt templates.

    Args:
        search: Search string to filter by ID

    Returns:
        List of prompt templates
    """
    try:
        templates = await service.get_all_templates(search=search)
        return BaseResponse(data=templates)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompt templates: {str(e)}",
        )


@router.put(
    "/{template_id}",
    status_code=status.HTTP_200_OK,
    name="Update Prompt Template",
    description="Update an existing prompt template",
    operation_id="update_prompt_template",
)
async def update_prompt_template(
    template_id: ULID,
    template_data: PromptTemplateCreateRequest,
    service: Annotated[PromptRegistry, Depends()],
) -> BaseResponse[PromptTemplateResponse]:
    """
    Update an existing prompt template.

    Args:
        template_id: The ID of the template to update
        template_data: The updated template data

    Returns:
        The updated template with its ID

    Raises:
        HTTPException: If template or document type doesn't exist or validation fails
    """
    try:
        template = await service.update_template(template_id, template_data)
        return BaseResponse(data=template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt template: {str(e)}",
        )
