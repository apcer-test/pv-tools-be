from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status
from fastapi_pagination import Page, Params

from apps.mail_box_config.schemas import (
    CreateUpdateMailBoxConfigRequest,
    MailBoxConfigDetailsResponse,
    MailBoxConfigResponse,
    UpdateMailBoxConfigRequest,
)
from apps.mail_box_config.services.mail_box_config import MailBoxService
from apps.users.models.user import Users
from apps.users.utils import current_user
from core.utils import BaseResponse
from core.utils.schema import SuccessResponse

router = APIRouter(prefix="/mail-box", tags=["Mail Box"])


@router.post(
    "/config",
    name="Create mail box config",
    description="Create mail box config",
    status_code=status.HTTP_200_OK,
    operation_id="create_mail_box_config",
)
async def configure_mail_box(
    request: Annotated[CreateUpdateMailBoxConfigRequest, Body()],
    service: Annotated[MailBoxService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[SuccessResponse]:
    """This function configures a new  mail box.
    :param user_id: is of the mail box to be configured
    :param request: CreateUserRequest
    :param service: UserService
    :return: CreateUserResponse
    """
    return BaseResponse(
        data=await service.add_mail_box_config(
            client_id=user.get("client").id, **request.model_dump()
        )
    )


@router.put(
    "/{mail_box_config_id}/config",
    name="Update Mail Box Configurations",
    description="Update mail box configurations",
    operation_id="update_user_configurations",
    status_code=status.HTTP_200_OK,
)
async def update_mail_box_configurations(
    mail_box_config_id: Annotated[str, Path()],
    request: Annotated[UpdateMailBoxConfigRequest, Body()],
    service: Annotated[MailBoxService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[SuccessResponse]:
    """This function updates a user configuration.
    :param mail_box_config_id: is of the mail box configuration to be updated
    :param request: CreateUserRequest
    :param service: UserService
    :return: CreateUserResponse
    """
    return BaseResponse(
        data=await service.update_mail_box_config(
            client_id=user.get("client").id,
            mail_box_config_id=mail_box_config_id,
            **request.model_dump()
        )
    )


@router.put(
    "/{mail_box_config_id}/status",
    name="Update Mail Box Configurations Status",
    description="Update mail box configurations status",
    operation_id="update_mail_box_configurations_status",
    status_code=status.HTTP_200_OK,
)
async def update_mail_box_configurations_status(
    mail_box_config_id: Annotated[str, Path()],
    service: Annotated[MailBoxService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[SuccessResponse]:
    """This function updates a user configuration.
    :param mail_box_config_id: is of the mail box configuration to be updated
    :param service: UserService
    :return: CreateUserResponse
    """
    return BaseResponse(
        data=await service.update_mail_box_config_status(
            client_id=user.get("client").id, mail_box_config_id=mail_box_config_id
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
    page_params: Annotated[Params, Depends()],
    service: Annotated[MailBoxService, Depends()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[Page[MailBoxConfigResponse]]:
    """This function retrieves all mail boxes.
    :param mail_box_id:
    :param service: UserService
    :return: CreateUserResponse
    """
    return BaseResponse(
        data=await service.get_mail_box_config_list(
            client_id=user.get("client").id, page_params=page_params
        )
    )


@router.get(
    "/{mail_box_config_id}/config",
    name="Get Mail Box Configurations By Id",
    description="Get mail box configurations by id",
    operation_id="get_mail_box_configurations_by_id",
    status_code=status.HTTP_200_OK,
)
async def get_mail_box_configurations_by_id(
    service: Annotated[MailBoxService, Depends()],
    mail_box_config_id: Annotated[str, Path()],
    user: Annotated[tuple[Users, str], Depends(current_user)],
) -> BaseResponse[MailBoxConfigDetailsResponse]:
    """This function retrieves a mail box configuration by id.
    :param mail_box_config_id: is of the mail box configuration to be retrieved
    :param service: UserService
    :return: MailBoxConfigResponse
    """
    return BaseResponse(
        data=await service.get_mail_box_config(
            mail_box_config_id=mail_box_config_id, client_id=user.get("client").id
        )
    )
