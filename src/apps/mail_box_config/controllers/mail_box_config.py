from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, status
from fastapi_pagination import Page, Params

from apps.mail_box_config.schemas import (
    CreateUpdateMailBoxConfigRequest,
    CreateUpdateMailBoxConfigResponse,
    MailBoxConfigResponse,
)
from core.auth import AdminHasPermission
from core.utils import BaseResponse
from core.utils.schema import SuccessResponse
from apps.mail_box_config.services.mail_box_config import MailBoxService

router = APIRouter(
    prefix="/{tenant_id}/mail-box",
    tags=["Mail Box"],
    dependencies=[Depends(AdminHasPermission())],
)


@router.post(
    "/config",
    name="Create mail box config",
    description="Create mail box config",
    status_code=status.HTTP_200_OK,
    operation_id="create_mail_box_config",
)
async def configure_mail_box(
    tenant_id: Annotated[str, Path()],
    request: Annotated[CreateUpdateMailBoxConfigRequest, Body()],
    service: Annotated[MailBoxService, Depends()],
) -> BaseResponse[CreateUpdateMailBoxConfigResponse]:
    """This function configures a new  mail box.
    :param user_id: is of the mail box to be configured
    :param request: CreateUserRequest
    :param service: UserService
    :return: CreateUserResponse
    """
    return BaseResponse(
        data=await service.add_mail_box_config(tenant_id=tenant_id, **request.model_dump())
    )


@router.put(
    "/{mail_box_config_id}/config",
    name="Update Mail Box Configurations",
    description="Update mail box configurations",
    operation_id="update_user_configurations",
    status_code=status.HTTP_200_OK,
)
async def update_mail_box_configurations(
    tenant_id: Annotated[str, Path()],
    mail_box_config_id: Annotated[UUID, Path()],
    request: Annotated[CreateUpdateMailBoxConfigRequest, Body()],
    service: Annotated[MailBoxService, Depends()],
) -> BaseResponse[CreateUpdateMailBoxConfigResponse]:
    """This function updates a user configuration.
    :param mail_box_config_id: is of the mail box configuration to be updated
    :param request: CreateUserRequest
    :param service: UserService
    :return: CreateUserResponse
    """
    return BaseResponse(
        data=await service.update_mail_box_config(
            tenant_id=tenant_id, mail_box_config_id=mail_box_config_id, **request.model_dump()
        )
    )


@router.get(
    "/configs",
    name="Get Mail Box Configurations",
    description="Get mail box configurations",
    operation_id="get_user_configurations",
    status_code=status.HTTP_200_OK,
)
async def get_mail_box_config_list(
    tenant_id: Annotated[str, Path()],
    page_params: Annotated[Params, Depends()],
    service: Annotated[MailBoxService, Depends()],
) -> BaseResponse[Page[MailBoxConfigResponse]]:
    """This function retrieves all mail boxes.
    :param mail_box_id:
    :param service: UserService
    :return: CreateUserResponse
    """
    return BaseResponse(
        data=await service.get_mail_box_config_list(
            tenant_id=tenant_id, page_params=page_params
        )
    )


@router.get(
    "/{mail_box_config_id}/config",
    name="Get Mail Box Configurations",
    description="Get mail box configurations",
    operation_id="get_all_users_configurations",
    status_code=status.HTTP_200_OK,
)
async def get_mail_box_configurations(
    service: Annotated[MailBoxService, Depends()],
    mail_box_config_id: Annotated[UUID, Path()],
    tenant_id: Annotated[str, Path()],
) -> BaseResponse[MailBoxConfigResponse]:
    """This function retrieves all users.
    :param mail_box_id:
    :param service: UserService
    :return: CreateUserResponse
    """
    return BaseResponse(
        data=await service.get_mail_box_config(
            mail_box_config_id=mail_box_config_id, tenant_id=tenant_id
        )
    )


@router.delete(
    "/{mail_box_config_id}",
    name="Delete mail box config",
    description="Delete mail box config",
    operation_id="delete_user_config",
    status_code=status.HTTP_200_OK,
)
async def delete_mail_box_config(
    tenant_id: Annotated[str, Path()],
    mail_box_config_id: Annotated[UUID, Path()],
    service: Annotated[MailBoxService, Depends()],
) -> BaseResponse[SuccessResponse]:
    """This function deletes a user configuration.
    :param mail_box_config_id: is of the mail box configuration to be deleted
    :param service: UserService
    :return: UserDeleteResponse
    """
    return BaseResponse(
        data=await service.delete_mail_box_config(
            tenant_id=tenant_id, mail_box_config_id=mail_box_config_id
        )
    )
