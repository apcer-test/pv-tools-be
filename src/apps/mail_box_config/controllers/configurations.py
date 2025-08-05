from typing import Annotated
from uuid import UUID

from fastapi import Body, Depends, Path
from fastapi import Request as FastAPIRequest
from fastapi import status
from fastapi.routing import APIRouter

from apps.admin.schemas.request import EncryptedRequest
from apps.mail_box_config.services.configurations import MicrosoftCredentialsService
from core.auth import AdminHasPermission
from core.utils.schema import BaseResponse

router = APIRouter(
    tags=["Microsoft Credentials"], dependencies=[Depends(AdminHasPermission())]
)


@router.patch(
    "/{tenant_id}/microsoft-credentials",
    status_code=status.HTTP_200_OK,
    name="Update Microsoft Credentials",
    description="This endpoint updates microsoft credentials.",
    operation_id="update_microsoft_credentials",
)
async def update_microsoft_credentials(
    request: FastAPIRequest,
    tenant_id: Annotated[str, Path()],
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[MicrosoftCredentialsService, Depends()],
) -> BaseResponse:
    """Update microsoft credentials.

    Args:
        body (GeneralSettingsBase): Partial configuration settings.
        service (TenantConfigurationService): Service to handle tenant settings.

    Returns:
        SuccessResponse: Updated configuration details in JSON format.
    """
    return BaseResponse(
        data=await service.update_microsoft_credentials(
            request=request, tenant_id=tenant_id, **body.model_dump(exclude_unset=True)
        )
    )


@router.get(
    "/{tenant_id}/microsoft-credentials",
    status_code=status.HTTP_200_OK,
    name="Get Tenant Configurations",
    description="This endpoint retrieves microsoft credentials.",
    operation_id="get_microsoft_credentials",
)
async def get_microsoft_credentials(
    tenant_id: Annotated[str, Path()],
    service: Annotated[MicrosoftCredentialsService, Depends()],
) -> BaseResponse:
    """Get microsoft credentials.

    Args:
        service (TenantConfigurationService): Service to handle tenant settings.

    Returns:
        SuccessResponse: Configuration details in JSON format.
    """
    return BaseResponse(
        data=await service.get_microsoft_credentials(tenant_id=tenant_id)
    )
