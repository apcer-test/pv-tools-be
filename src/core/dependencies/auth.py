from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt.api_jwt as jwt
from fastapi import Depends, Path, Request
from fastapi.security import (
    APIKeyCookie,
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt.exceptions import DecodeError, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.clients.models.clients import Clients
from apps.users.constants import UserAuthAction
from config import settings
from core.constants import AuthTokenType, ErrorMessage
from core.db import db_session
from core.exceptions import ForbiddenError, UnauthorizedError
from core.utils.crypto import CryptoUtil
from core.utils.hashing import verify_hash

access_scheme_header = HTTPBearer(scheme_name="Access Token", auto_error=False)
access_scheme_cookie = APIKeyCookie(
    name="AccessCookie", scheme_name="Access Cookie", auto_error=False
)
refresh_scheme_header = HTTPBearer(scheme_name="Refresh Token", auto_error=False)
refresh_scheme_cookie = APIKeyCookie(
    name="RefreshCookie", scheme_name="Refresh Cookie", auto_error=False
)
access_key_scheme_header = APIKeyHeader(
    name="access-key", scheme_name="Access Key Header", auto_error=False
)
secret_key_scheme_header = APIKeyHeader(
    name="secret-key", scheme_name="Secret Key Header", auto_error=False
)


class Authentication:
    """JWT utility class for token encoding and decoding."""

    def __init__(self, token_type: AuthTokenType) -> None:
        self.token_type = token_type
        self.options = {"verify_aud": False, "verify_nbf": False}

    def encode(
        self,
        subject: int,
        jwt_secret: str,
        jwt_algorithm: str,
        exp: int,
        **additional_claims: str | float | bool | None,
    ) -> str:
        for k, v in additional_claims.items():
            if not isinstance(v, str):
                additional_claims[k] = str(v)
        return jwt.encode(
            payload={
                "sub": str(subject),
                "iss": settings.COMPANY_NAME,
                "iat": datetime.now(tz=UTC),
                "exp": datetime.now(tz=UTC) + timedelta(minutes=exp),
                **additional_claims,
            },
            key=jwt_secret,
            algorithm=jwt_algorithm,
        )

    def decode(self, token: str, jwt_secret: str, jwt_algorithm: str) -> dict[str, str]:
        try:
            payload = jwt.decode(
                token,
                key=jwt_secret,
                algorithms=[jwt_algorithm],
                options=self.options,
                issuer=settings.COMPANY_NAME,
            )

            if payload.get("type") != self.token_type:
                raise UnauthorizedError(ErrorMessage.INVALID_JWT_TOKEN)

            return payload  # noqa: TRY300

        except ExpiredSignatureError as exc:
            raise UnauthorizedError(ErrorMessage.EXPIRED_TOKEN) from exc

        except DecodeError as exc:
            raise UnauthorizedError(ErrorMessage.INVALID_JWT_TOKEN) from exc


class AccessAuthentication(Authentication):
    """Access token authentication."""

    def __init__(self) -> None:
        super().__init__("access")

    async def __call__(
        self,
        header_token: Annotated[
            HTTPAuthorizationCredentials | None, Depends(access_scheme_header)
        ],
        cookie_token: Annotated[str | None, Depends(access_scheme_cookie)],
    ) -> str:
        """Return token from header or cookie."""
        if header_token:
            return header_token.credentials
        if cookie_token:
            return cookie_token
        raise UnauthorizedError(ErrorMessage.UNAUTHORIZED)


class RefreshAuthentication(Authentication):
    """Refresh token authentication."""

    def __init__(self) -> None:
        super().__init__("refresh")

    async def __call__(
        self,
        header_token: Annotated[
            HTTPAuthorizationCredentials | None, Depends(refresh_scheme_header)
        ],
        cookie_token: Annotated[str | None, Depends(refresh_scheme_cookie)],
    ) -> str:
        """Return token from header or cookie."""
        if header_token:
            return header_token.credentials
        if cookie_token:
            return cookie_token
        raise UnauthorizedError(ErrorMessage.UNAUTHORIZED)


access_jwt = AccessAuthentication()
refresh_jwt = RefreshAuthentication()


async def _get_client(session: AsyncSession, client_slug: str) -> Clients:
    stmt = (
        select(Clients)
        .where(Clients.slug == client_slug, Clients.deleted_at.is_(None))
    )
    result = await session.execute(stmt)
    client = result.scalar_one_or_none()

    if not client:
        raise UnauthorizedError(ErrorMessage.UNAUTHORIZED)
    return client


async def verify_api_keys(
    access_key: Annotated[str | None, Depends(access_key_scheme_header)],
    secret_key: Annotated[str | None, Depends(secret_key_scheme_header)],
    app_key: Annotated[int | str, Path()],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> tuple[str, str, str]:
    """
    Verifies the provided access key and secret key against the database.

    Args:
        access_key (str | None): API access key from request header.
        secret_key (str | None): API secret key from request header.
        session (AsyncSession): Database session for querying tenant info.

    Returns:
        tuple[str, str, str]: Tuple containing validated access_key, secret_key,
        and tenant's stored secret_key.

    Raises:
        UnauthorizedError: If either key is missing or validation fails.
    """
    if access_key and secret_key:
        try:
            client_query = Clients.id == int(app_key)
        except (ValueError, TypeError):
            client_query = Clients.slug == app_key

        stmt = select(Clients).where(
            client_query,
            Clients.deleted_at.is_(None),
            Clients.access_key == access_key,
        )
        result = await session.execute(stmt)
        client = result.scalar_one_or_none()

        if client:
            is_secret_match = verify_hash(
                incoming_key=secret_key, stored_hash=client.secret_key
            )
            if is_secret_match:
                return True
            raise ForbiddenError(ErrorMessage.FORBIDDEN)

    raise ForbiddenError(ErrorMessage.FORBIDDEN)

async def verify_access_token(
    token: Annotated[str, Depends(access_jwt)],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> dict[str, Any]:
    """Verify the access token."""
    return token