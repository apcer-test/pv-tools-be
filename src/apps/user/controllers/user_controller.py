from typing import Annotated
from uuid import UUID

from authlib.integrations.base_client import OAuthError
from fastapi import APIRouter, Body, Depends, Path, Query, Request, status
from fastapi.responses import JSONResponse
import httpx
from starlette.responses import RedirectResponse

import constants
from apps.user.models.user import UserModel
from apps.user.schemas.request import EncryptedRequest
from apps.user.schemas.response import BaseUserResponse
from apps.user.services import UserService
from apps.user.services.microsoft_sso import MicrosoftSSOService
from core.auth import AdminHasPermission, HasPermission
from core.types import Providers, RoleType
from core.utils.schema import BaseResponse
from core.utils.set_cookies import set_auth_cookies
from config import AppEnvironment, settings
from core.utils import logger
from core.utils.sso_client import SSOOAuthClient

router = APIRouter(prefix="/api/user", tags=["User"])

@router.get(
    "/openid/login/{provider}",
    status_code=status.HTTP_200_OK,
    response_description="",
    name="login",
    description="endpoint for login using provider",
    operation_id="sso_login",
)
async def login_by_provider(request: Request, provider: Annotated[Providers, Path()]) -> RedirectResponse:
    """
    Open api provider login function
    """
    print("LOGIN: session before redirect:", request.session)
    try:
        match provider:
            case Providers.MICROSOFT:
                if settings.ENV == AppEnvironment.LOCAL:
                    redirect_uri = request.url_for("sso_auth_callback", provider=provider.value)
                else:
                    redirect_uri = f"{settings.SOCIAL_AUTH_REDIRECT_URL}/{settings.SOCIAL_AUTH_ENDPOINT}/{provider}"
                redirect_uri = f"{redirect_uri}?client_ids=123"
                return (
                    await SSOOAuthClient(provider.value)
                    .oauth.create_client(provider.value)
                    .authorize_redirect(request, redirect_uri)
                )

            case _:
                return RedirectResponse(url=settings.UI_LOGIN_SCREEN)
    except Exception as e:
        logger.error(f"SSO login error for provider {provider}: {str(e)}")
        return RedirectResponse(url=settings.UI_LOGIN_SCREEN)

@router.get(
    "/{provider}",
    status_code=status.HTTP_200_OK,
    name="sso_auth_callback",
    description="callback endpoint for auth using provider",
    operation_id="sso_auth_callback",
)
async def auth(
    request: Request,
    client_ids: Annotated[str, Query()],
    service: Annotated[MicrosoftSSOService, Depends()],
    provider: Annotated[Providers, Path()]
) -> RedirectResponse:
    """
    get details by provider
    """
    print("AUTH: session on callback:", request.session)
    print(f"client_ids: {client_ids}")
    try:
        match provider:
            case Providers.MICROSOFT:
                try:
                    user_data = {}

                    # Get access token
                    token = (
                        await SSOOAuthClient(provider.value)
                        .oauth.create_client(provider.value)
                        .authorize_access_token(request)
                    )
            
                    print(f"token: {token}")
                    if not token:
                        logger.error("Failed to get access token from Microsoft")
                        return RedirectResponse(url=settings.UI_LOGIN_SCREEN)

                    # Get ID token claims
                    user_data.update(
                        await SSOOAuthClient(provider.value)
                        .oauth.create_client(provider.value)
                        .parse_id_token(token, nonce=request.session.get("nonce"))
                    )

                    # Get user info
                    user_data.update(
                        await SSOOAuthClient(provider.value)
                        .oauth.create_client(provider.value)
                        .userinfo(token=token)
                    )

                    logger.info(f"Successfully got user data from Microsoft: {user_data.get('email')}")
                    return {"user_data": user_data}

                except OAuthError as oauth_error:
                    logger.error(f"OAuth error during Microsoft callback: {str(oauth_error)}")
                    return RedirectResponse(url=settings.UI_LOGIN_SCREEN)
                except Exception as e:
                    logger.error(f"Unexpected error during Microsoft callback: {str(e)}")
                    return RedirectResponse(url=settings.UI_LOGIN_SCREEN)
                finally:
                    # Clean up session
                    request.session.clear()

            case _:
                logger.warning(f"Unsupported provider in callback: {provider}")
                return RedirectResponse(url=settings.UI_LOGIN_SCREEN)
    except Exception as e:
        logger.error(f"Global error in auth callback: {str(e)}")
        return RedirectResponse(url=settings.UI_LOGIN_SCREEN)