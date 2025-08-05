from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.ai_extraction.schemas.response import DocumentTypeResponse
from apps.ai_extraction.services.doctype import DocTypeService
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/api/doc-types", tags=["Document Types"])


@router.get(
    "/get-all-doc-types",
    status_code=status.HTTP_200_OK,
    name="Get All Document Types",
    description="Get all document types with their prompt templates and extraction agents",
    operation_id="get_all_doc_types",
    response_model=BaseResponse[List[DocumentTypeResponse]],
    responses={
        200: {"description": "List of document types with related data"},
        404: {"description": "No document types found"},
    },
)
async def get_all_doc_types(
    service: Annotated[DocTypeService, Depends()],
    search: Optional[str] = Query(
        None, description="Search by document type ID or code"
    ),
) -> BaseResponse[List[DocumentTypeResponse]]:
    """
    Retrieve all document types with their related data.

    This endpoint returns a list of all document types with their prompt templates
    and extraction agents.

    Returns:
        BaseResponse[List[DocumentTypeResponse]]: List of document types with related data

    Raises:
        HTTPException: If no document types are found
    """
    try:
        doc_types = await service.get_all_doc_types(search=search)
        return BaseResponse(data=doc_types)
    except HTTPException as e:
        # Re-raise the HTTPException to return the appropriate status code
        raise e
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching document types: {str(e)}",
        )
