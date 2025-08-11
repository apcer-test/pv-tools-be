from typing import Annotated
from fastapi import APIRouter, Body, Depends, UploadFile, File, status, Query, Path

from core.utils.schema import BaseResponse, SuccessResponse
from apps.master_modules.services.setup import SetupService
from core.types import LookupType
from core.utils.pagination import PaginatedResponse, PaginationParams
from apps.master_modules.schemas.response import LookupResponse
from apps.master_modules.schemas.request import (
    CodeListLookupValueCreateRequest,
    NFListLookupValueCreateRequest,
    UpdateLookupValueStatusRequest,
    LookupValuesBySlugsRequest,
)

router = APIRouter(prefix="/setup", tags=["Setup"])

@router.post(
    "/upload-excel",
    status_code=status.HTTP_200_OK,
    name="Upload Excel file for master setup data",
    description="Upload an Excel file containing master setup data. The file should have a sheet named 'Lookup' and 'Lookup Values' with required columns.",
    operation_id="upload_excel_file",
)
async def upload_excel_file(
    file: Annotated[UploadFile, File(...)],
    service: Annotated[SetupService, Depends()]
) -> BaseResponse[SuccessResponse]:
    """
    Upload an Excel file containing master setup data.
    The file should have a sheet named 'Lookup' and 'Lookup Values' with required columns.
    """
    return BaseResponse(data = await service.process_excel_file(file=file))

@router.get(
    "/lookup",
    status_code=status.HTTP_200_OK,
    name="Get lookup list",
    description="Get list of all active lookup entries with their id, name, slug and type.",
    operation_id="get_lookup_list",
)
async def get_lookup_list(
    service: Annotated[SetupService, Depends()],
    lookup_type_filter: Annotated[LookupType, Query(default=None, description="Filter lookups by type ('code-list' or 'nf-list')")] | None = None,
    page: Annotated[int, Query(1, ge=1, description="Page number")] | None = 1,
    page_size: Annotated[int, Query(10, ge=1, le=100, description="Items per page")] | None = 10,
    search: Annotated[str | None, Query(None, description="Search by lookup name (contains, case-insensitive)")] | None = None,
) -> BaseResponse[PaginatedResponse[LookupResponse]]:
    """
    Get list of all active lookup entries.
    Returns a list of lookup entries with their id, name, slug and type.
    """
    pagination_params = PaginationParams(page=page, page_size=page_size, search=search)
    return BaseResponse(
        data=await service.get_lookup_list(
            lookup_type_filter=lookup_type_filter, params=pagination_params
        )
    )

@router.get(
    "/lookup/{lookup_id}/values",
    status_code=status.HTTP_200_OK,
    name="Get lookup values by lookup id",
    description="Get paginated list of lookup values for a given lookup id.",
    operation_id="get_lookup_values",
)
async def get_lookup_values(
    lookup_id: Annotated[str, Path(..., description="Lookup id")],
    service: Annotated[SetupService, Depends()],
    page: Annotated[int, Query(1, ge=1, description="Page number")] | None = 1,
    page_size: Annotated[int, Query(10, ge=1, le=100, description="Items per page")] | None = 10,
    search: Annotated[str | None, Query(None, description="Search by value name (contains, case-insensitive)")] | None = None,
) -> BaseResponse:
    """
    Return lookup values for a specific lookup. Response shape is inferred from the lookup type.
    """
    pagination_params = PaginationParams(page=page, page_size=page_size, search=search)
    return BaseResponse(
        data=await service.get_lookup_values(
            lookup_id=lookup_id, params=pagination_params
        )
    )

@router.post(
    "/lookup/{lookup_id}/codelist/values",
    status_code=status.HTTP_201_CREATED,
    name="Create code-list lookup value",
    description="Create a lookup value for a given lookup id (code-list).",
    operation_id="create_lookup_value",
)
async def create_lookup_value(
    lookup_id: Annotated[str, Path(..., description="Lookup id")],
    body: Annotated[CodeListLookupValueCreateRequest, Body(..., description="Request body")],
    service: Annotated[SetupService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """Create lookup value with name, r2, r3; is_active=True by default."""
    return BaseResponse(
        data=await service.create_codelist_lookup_value(lookup_id=lookup_id, **body.model_dump())
    )

@router.post(
    "/lookup/{lookup_id}/nflist/values",
    status_code=status.HTTP_201_CREATED,
    name="Create nf-list lookup value",
    description="Create an nf-list lookup value for a given lookup id.",
    operation_id="create_nf_lookup_value",
)
async def create_nf_lookup_value(
    lookup_id: Annotated[str, Path(..., description="Lookup id")],
    body: Annotated[NFListLookupValueCreateRequest, Body(..., description="Request body")],
    service: Annotated[SetupService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """Create nf-list lookup value with name; is_active=True by default."""
    return BaseResponse(
        data=await service.create_nflist_lookup_value(lookup_id=lookup_id, **body.model_dump())
    )

@router.put(
    "/lookup/values/{lookup_value_id}/status",
    status_code=status.HTTP_200_OK,
    name="Update lookup value status",
    description="Update is_active for a lookup value by its id.",
    operation_id="update_lookup_value_status",
)
async def update_lookup_value_status(
    lookup_value_id: Annotated[str, Path(..., description="Lookup value id")],
    body: Annotated[UpdateLookupValueStatusRequest, Body(..., description="Request body")],
    service: Annotated[SetupService, Depends()],
) -> BaseResponse[SuccessResponse]:
    return BaseResponse(
        data=await service.update_lookup_value_status(lookup_value_id=lookup_value_id, **body.model_dump())
    )


@router.post(
    "/lookup/values-by-slugs",
    status_code=status.HTTP_200_OK,
    name="Get lookup values by slugs",
    description=(
        "Accepts a list of slugs and returns a mapping from slug to its list of lookup values. "
        "If a slug is not found, an empty list is returned for that slug."
    ),
    operation_id="get_lookup_values_by_slugs",
)
async def get_lookup_values_by_slugs(
    body: Annotated[LookupValuesBySlugsRequest, Body(..., description="Request body")],
    service: Annotated[SetupService, Depends()],
) -> BaseResponse[dict[str, list[dict]]]:
    return BaseResponse(data=await service.get_lookup_values_by_slugs(**body.model_dump()))
