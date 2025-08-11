"""Case management controller module."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

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
    """Create a new case number configuration.

    Args:
        config: Configuration to create
        service: Case service instance

    Returns:
        Created configuration

    Raises:
        HTTPException: If validation fails
    """
    result = await service.create_configuration(config)
    return BaseResponse(data=result)


@router.get(
    "/configurations",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[list[CaseNumberConfigurationResponse]],
    name="List Case Number Configurations",
    description="List all case number configurations with optional active status filter",
    operation_id="list_case_configurations",
)
async def list_configurations(
    service: Annotated[CaseService, Depends()],
    is_active: Annotated[
        Optional[bool], Query(description="Filter by active status (true/false)")
    ] = None,
) -> BaseResponse[list[CaseNumberConfigurationResponse]]:
    """List all case number configurations.

    Args:
        service: Case service instance
        is_active: Optional filter for active status (true/false)

    Returns:
        List of configurations matching the filter
    """
    result = await service.list_configurations(is_active=is_active)
    return BaseResponse(data=result)


@router.put(
    "/configurations/{config_id}/active",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[CaseNumberConfigurationResponse],
    name="Set Active Configuration",
    description="Set a configuration as active",
    operation_id="set_active_configuration",
)
async def set_configuration_active(
    config_id: str, service: Annotated[CaseService, Depends()]
) -> BaseResponse[CaseNumberConfigurationResponse]:
    """Set a configuration as active.

    Args:
        config_id: ID of the configuration to activate
        service: Case service instance

    Returns:
        BaseResponse containing the activated configuration
    """
    result = await service.set_configuration_active(config_id)
    return BaseResponse(data=result)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponse[CaseResponse],
    name="Create Case",
    description="Create a new case",
    operation_id="create_case",
)
async def create_case(
    case: CaseCreate, service: Annotated[CaseService, Depends()]
) -> BaseResponse[CaseResponse]:
    """Create a new case.

    Args:
        case: Case to create
        service: Case service instance

    Returns:
        BaseResponse containing the created case
    """
    result = await service.create_case(case)
    return BaseResponse(data=result)


@router.get(
    "/{case_number}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[CaseResponse],
    name="Get Case",
    description="Get a case by ID",
    operation_id="get_case",
)
async def get_case(
    case_number: str, service: Annotated[CaseService, Depends()]
) -> BaseResponse[CaseResponse]:
    """Get a case by ID.

    Args:
        case_number: ID of the case to retrieve
        service: Case service instance

    Returns:
        BaseResponse containing the case details
    """
    result = await service.get_case(case_number)
    return BaseResponse(data=result)


@router.patch(
    "/configurations/{config_id}",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponse[CaseNumberConfigurationResponse],
    name="Update Case Number Configuration",
    description="Update an existing case number configuration",
    operation_id="update_case_configuration",
)
async def update_configuration(
    config_id: str,
    config: CaseNumberConfigurationCreate,
    service: Annotated[CaseService, Depends()],
) -> BaseResponse[CaseNumberConfigurationResponse]:
    """Update a case number configuration.

    Args:
        config_id: Configuration ID to update
        config: Updated configuration data
        service: Case service instance

    Returns:
        Updated configuration

    Raises:
        HTTPException: If validation fails or configuration not found
    """

    result = await service.update_configuration(config_id, config)
    return BaseResponse(data=result)
