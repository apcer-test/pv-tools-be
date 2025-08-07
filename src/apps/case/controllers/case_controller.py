from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from apps.case.schemas.request import CaseCreate, CaseNumberConfigurationCreate
from apps.case.schemas.response import CaseNumberConfigurationResponse, CaseResponse
from apps.case.services.case_service import CaseService
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.post(
    "/configurations",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponse[CaseNumberConfigurationResponse],
    name="Create Case Number Configuration",
    description="Create a new case number configuration",
    operation_id="create_case_configuration",
)
async def create_configuration(
    config: CaseNumberConfigurationCreate, service: Annotated[CaseService, Depends()]
) -> BaseResponse[CaseNumberConfigurationResponse]:
    """Create a new case number configuration"""
    result = await service.create_configuration(config)
    return BaseResponse(data=result)


@router.put(
    "/configurations/{config_id}/active",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[CaseNumberConfigurationResponse],
    name="Set Configuration Active",
    description="Set a configuration as active and deactivate others",
    operation_id="set_configuration_active",
)
async def set_configuration_active(
    config_id: str, service: Annotated[CaseService, Depends()]
) -> BaseResponse[CaseNumberConfigurationResponse]:
    """Set a configuration as active"""

    result = await service.set_configuration_active(config_id)
    return BaseResponse(data=result)


@router.get(
    "/configurations",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[List[CaseNumberConfigurationResponse]],
    name="List Case Number Configurations",
    description="List all case number configurations",
    operation_id="list_case_configurations",
)
async def list_configurations(
    active_only: bool, service: Annotated[CaseService, Depends()]
) -> BaseResponse[List[CaseNumberConfigurationResponse]]:
    """List all case number configurations"""
    result = await service.list_configurations(active_only)
    return BaseResponse(data=result)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponse[CaseResponse],
    name="Create Case",
    description="Create a new case with generated case number",
    operation_id="create_case",
)
async def create_case(
    case: CaseCreate, service: Annotated[CaseService, Depends()]
) -> BaseResponse[CaseResponse]:
    """Create a new case with generated case number"""
    result = await service.create_case(case)
    return BaseResponse(data=result)


@router.get(
    "/{case_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[CaseResponse],
    name="Get Case",
    description="Get a case by ID",
    operation_id="get_case",
)
async def get_case(
    case_number: str, service: Annotated[CaseService, Depends()]
) -> BaseResponse[CaseResponse]:
    """Get a case by ID"""
    result = await service.get_case(case_number)
    return BaseResponse(data=result)
