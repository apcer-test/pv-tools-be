import secrets
import string
from typing import Annotated, Any

from fastapi import Path
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.tenant_app_configs.constants import JWTClaimsEnum, OTPTypeEnum
from apps.tenant_app_configs.exceptions import TenantAppConfigNotFoundError
from apps.tenant_app_configs.models import TenantAppConfig
from apps.users.constants import UserAuthAction
from apps.users.models import Users
from apps.users.schemas.response import AdditionalClaimsResponse
from core.constants import ErrorMessage
from core.db import db_session
from core.dependencies import (
    access_jwt,
    verify_access_token,
    verify_purpose_access_token,
)
from core.exceptions import UnauthorizedError
from core.utils.resolve_context_ids import get_context_ids_from_keys


async def get_user_id_from_access_token(
    token_claims: Annotated[dict[str, Any], Depends(verify_access_token)],
) -> int:
    """Fetch the user ID from the token claims.

    :param token_claims: The token payload.
    :return: The user ID.
    """
    user_id = token_claims.get("sub")
    if not user_id:
        raise UnauthorizedError(message=ErrorMessage.UNAUTHORIZED)

    return int(user_id)


async def get_session_id_from_token(
    token_claims: Annotated[dict[str, Any], Depends(verify_access_token)],
) -> str | None:
    """Fetch the session ID from the token claims.

    :param token_claims: The token payload.
    :return: The session ID.
    """
    return token_claims.get("session_id")


def generate_otp(otp_length: int, otp_type: OTPTypeEnum) -> str:
    """Generate a cryptographically secure OTP code."""

    if otp_type == OTPTypeEnum.NUMERIC:
        return "".join(secrets.choice(string.digits) for _ in range(otp_length))
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(otp_length)
    )


async def current_user(
    tenant_key: Annotated[int | str, Path()],
    app_key: Annotated[int | str, Path()],
    user_id: Annotated[int, Depends(get_user_id_from_access_token)],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> Users:
    """Fetch the tenant user and return it.

    :param token_claims: The token payload.
    :param session: The database session.
    :param tenant_id (int): the tenant's id

    :return: The user object.
    """

    tenant_id, app_id = await get_context_ids_from_keys(
        session=session, tenant_key=tenant_key, app_key=app_key
    )
    user = await session.scalar(
        select(Users).where(
            Users.tenant_id == tenant_id, Users.app_id == app_id, Users.id == user_id
        )
    )
    if not user:
        raise UnauthorizedError(message=ErrorMessage.UNAUTHORIZED)

    return user


async def get_tenant_app_config(
    tenant_key: Annotated[int | str, Path()],
    app_key: Annotated[int | str, Path()],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> TenantAppConfig:
    tenant_id, app_id = await get_context_ids_from_keys(
        session=session, tenant_key=tenant_key, app_key=app_key
    )
    app_config = await session.scalar(
        select(TenantAppConfig).where(
            TenantAppConfig.tenant_id == tenant_id, TenantAppConfig.app_id == app_id
        )
    )
    if not app_config:
        raise TenantAppConfigNotFoundError
    return app_config


async def verify_change_password_token(
    token: Annotated[str, Depends(access_jwt)],
    session: Annotated[AsyncSession, Depends(db_session)],
    app_key: Annotated[int | str, Path()],
) -> TenantAppConfig:
    return await verify_purpose_access_token(
        token=token,
        session=session,
        app_key=app_key,
        req_purpose=UserAuthAction.CHANGE_PASSWORD,
    )


def get_jwt_additional_claims(
    additional_claims: list[JWTClaimsEnum] | None = None,
    email: str | None = None,
    is_mfa_enabled: bool | None = None,
    roles: list[str] | None = None,
) -> AdditionalClaimsResponse:
    # If no additional_claims provided, return empty response
    if not additional_claims:
        return AdditionalClaimsResponse()

    # Map all possible claim enums to their actual values
    available_claims = {
        JWTClaimsEnum.EMAIL: email,
        JWTClaimsEnum.ROLES: roles,
        JWTClaimsEnum.IS_MFA_ENABLED: (
            "true"
            if is_mfa_enabled
            else "false" if is_mfa_enabled is not None else None
        ),
    }

    # Build dict of requested and non-None claims
    filtered_claims = {
        claim.value: value
        for claim, value in available_claims.items()
        if claim in additional_claims and value is not None
    }

    return AdditionalClaimsResponse(**filtered_claims)
