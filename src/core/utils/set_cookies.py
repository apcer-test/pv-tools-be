import json

from fastapi.responses import JSONResponse
from ulid import ULID

from config import settings
from core.db import redis
from core.types import RoleType
from core.utils.hashing import Hash


def set_auth_cookies(
    response: JSONResponse, tokens: dict[str, str], role: RoleType
) -> JSONResponse:
    """
    Set authentication cookies in an HTTP response.
    This function takes an HTTP response object and a dictionary of tokens, and sets two cookies,
    "accessToken" and "refreshToken," in the response. These cookies are used for user authentication.
    Args:
        response (Response): The HTTP response object to set cookies in.
        tokens (dict[str, str]): A dictionary containing access and refresh tokens.
        role (role-type): A role type of user
    Returns:
        Response: The updated HTTP response with the authentication cookies set.
    """
    cookies_params = {
        "domain": settings.COOKIES_DOMAIN,
        "secure": True,
        "samesite": "lax" if settings.is_production else "none",
        "httponly": True,
    }

    if role == RoleType.USER:
        response.set_cookie(
            "accessToken",
            tokens["access_token"],
            expires=int(settings.ACCESS_TOKEN_EXP),
            **cookies_params,
        )
        response.set_cookie(
            "refreshToken",
            tokens["refresh_token"],
            expires=int(settings.REFRESH_TOKEN_EXP),
            **cookies_params,
        )
    if role == RoleType.ADMIN:
        response.set_cookie(
            "adminAccessToken",
            tokens["access_token"],
            expires=int(settings.ACCESS_TOKEN_EXP),
            **cookies_params,
        )
        response.set_cookie(
            "adminRefreshToken",
            tokens["refresh_token"],
            expires=int(settings.REFRESH_TOKEN_EXP),
            **cookies_params,
        )
    return response


def delete_cookies(response: JSONResponse, role: RoleType) -> JSONResponse:
    """
    Delete authentication cookies from an HTTP response.
    This function takes an HTTP response object and removes the "accessToken" and "refreshToken" cookies
    from the response, making them invalid for subsequent requests.
    Args:
        response (Response): The HTTP response object to remove cookies from.
        role(Role type): The role type of user.
    Returns:
        Response: The updated HTTP response with the cookies removed.
    """
    cookie_params = {
        "domain": settings.COOKIES_DOMAIN,
        "secure": True,
        "samesite": "lax" if settings.is_production else "none",
        "httponly": False,
    }

    if role == RoleType.USER:
        response.delete_cookie("accessToken", **cookie_params)
        response.delete_cookie("refreshToken", **cookie_params)
    elif role == RoleType.ADMIN:
        response.delete_cookie("adminAccessToken", **cookie_params)
        response.delete_cookie("adminRefreshToken", **cookie_params)

    return response


async def create_user_token_caching(
    tokens: dict, user_id: ULID, client_slug: str
) -> None:
    """
     Create caching for access-token and refresh-token.
    :param user_id:
    :param tokens: access-token and refresh-token
    :return: None
    """
    hashed_user_id = Hash.make("uid:" + str(user_id) + ":" + client_slug)
    if settings.IS_SINGLE_DEVICE_LOGIN_ENABLED:
        await delete_user_previous_tokens(user_id=user_id, client_slug=client_slug)
    dumped_data = json.dumps(
        {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
        }
    )
    await redis.set(
        name=hashed_user_id, value=dumped_data, ex=settings.ACCESS_TOKEN_EXP
    )
    await create_tokens_caching(tokens)


async def create_tokens_caching(tokens: dict) -> None:
    """
    Create caching for access-token and refresh-token.
    :param tokens: access-token and refresh-token
    :return: None
    """
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    dumped_data = json.dumps(
        {"access_token": access_token, "refresh_token": refresh_token}
    )
    access_token_key = Hash.make(access_token)
    refresh_token_key = Hash.make(refresh_token)
    await redis.set(
        name=access_token_key, value=dumped_data, ex=settings.ACCESS_TOKEN_EXP
    )
    await redis.set(
        name=refresh_token_key, value=dumped_data, ex=settings.REFRESH_TOKEN_EXP
    )


async def delete_user_previous_tokens(user_id: ULID, client_slug: str) -> None:
    """
    Create caching for access-token and refresh-token.
    :param user_id:
    :return: None
    """
    hashed_user_id = Hash.make("uid:" + str(user_id) + ":" + client_slug)
    get_active_user = await redis.get(name=hashed_user_id)
    if get_active_user:
        old_access_token = json.loads(get_active_user).get("access_token")
        old_refresh_token = json.loads(get_active_user).get("refresh_token")
        await redis.delete(hashed_user_id)
        await redis.delete(Hash.make(old_access_token))
        await redis.delete(Hash.make(old_refresh_token))
