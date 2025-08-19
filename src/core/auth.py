from datetime import datetime, timedelta
from typing import Annotated, Any, Literal

from fastapi import Cookie, Depends, Request
from fastapi.openapi.models import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer as HTTPBearerSecurity
from fastapi.security.base import SecurityBase
from jwt import DecodeError, ExpiredSignatureError, decode, encode

import constants.messages as constants
from config import settings
from core.db import redis
from core.exceptions import InvalidJWTTokenException, UnauthorizedError
from core.utils.hashing import Hash


async def check_cached_token_exists(token: str) -> None:
    """
    Check the cached token is existed or not.
    :param token: access token or refresh token
    :return: None
    """
    key = Hash.make(token)
    exist_token = await redis.get(key)
    if not exist_token:
        raise UnauthorizedError(message=constants.UNAUTHORIZED)


class JWToken(SecurityBase):
    """
    A class for handling JWT tokens.

    This class inherits from :class:`SecurityBase` and provides methods for encoding and decoding JWT tokens.

    Args:
        token_type (Literal["access", "refresh"]): The type of token.

    Attributes:
        model: The HTTPBearer model for token extraction.
        scheme_name: The name of the token scheme.
        token_type (Literal["access", "refresh"]): The type of token.
    """

    def __init__(self, token_type: Literal["access", "refresh"]) -> None:
        """
        Initialize the JWToken with the specified token type.

        Args:
            token_type (Literal["access", "refresh"]): The type of token.
        """
        self.model = HTTPBearer(name=f"{token_type}Token")
        self.scheme_name = self.__class__.__name__
        self.token_type = token_type

    def encode(self, payload: dict, expire_period: int = 3600) -> str:
        """
        Encode a payload into a JWT token.

        Args:
            payload (dict): The payload to be included in the token.
            expire_period (int, optional): The expiry period of the token in seconds. Defaults to 3600.

        Returns:
            str: The encoded JWT token.
        """
        return encode(
            {
                **payload,
                "type": self.token_type,
                "exp": datetime.utcnow() + timedelta(seconds=expire_period),
            },
            key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def decode(self, token: str) -> dict[str, Any] | None:
        """
        Decode a JWT token.

        Args:
            token (str): The JWT token to decode.

        Returns:
            Union[dict[str, Any], None]: The decoded token payload.
        """
        try:
            payload = decode(
                token,
                key=settings.JWT_SECRET_KEY,
                algorithms=settings.JWT_ALGORITHM,
                option={"verify_signature": True, "verify_exp": True},
            )
            if payload.get("type") != self.token_type:
                raise UnauthorizedError(constants.UNAUTHORIZED)
            return payload
        except DecodeError:
            raise InvalidJWTTokenException(constants.INVALID_TOKEN)
        except ExpiredSignatureError:
            raise InvalidJWTTokenException(constants.EXPIRED_TOKEN)

    async def __call__(
        self,
        request: Request,
        access_token: Annotated[
            str | None, Cookie(alias="accessToken", include_in_schema=False)
        ] = None,  # type: ignore
        refresh_token: Annotated[
            str | None, Cookie(alias="refreshToken", include_in_schema=False)
        ] = None,  # type: ignore
        authorization: Annotated[
            HTTPAuthorizationCredentials, Depends(HTTPBearerSecurity(auto_error=False))
        ] = None,
    ) -> dict[str, Any] | None:
        """
        Extract the token from the request and decode it.

        Args:
            request (Request): The incoming request.
            access_token (str | None, optional): The access token cookie. Defaults to None.
            refresh_token (str | None, optional): The refresh token cookie. Defaults to None.

        Returns:
            Union[dict[str, Any], None]: The decoded token payload or None if no token found.
        """
        if authorization:
            try:
                token = authorization.credentials
                await check_cached_token_exists(token)
                return self.decode(token)
            except InvalidJWTTokenException:
                raise UnauthorizedError(message=constants.UNAUTHORIZED)

        token_mapping = {
            constants.ACCESS: access_token,
            constants.REFRESH: refresh_token,
        }

        token = token_mapping.get(self.token_type)

        if token:
            await check_cached_token_exists(token)
            return self.decode(token)

        if self.token_type in [constants.ACCESS, constants.REFRESH]:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)
        return None


access = JWToken("access")
refresh = JWToken("refresh")
