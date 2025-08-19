import base64
import json
import re
import secrets
from datetime import datetime, timedelta, timezone

import sentry_sdk
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as crypto_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from pydantic import EmailStr
from sqlalchemy import select

import constants
from apps.mail_box_config.models.credentials import MicrosoftCredentialsConfig
from apps.mail_box_config.models.mail_box import MicrosoftMailBoxConfig
from apps.tenant.models.models import Tenant
from apps.users.exceptions import (
    EmptyDescriptionException,
    InvalidEmailException,
    InvalidEncryptedData,
    InvalidPhoneFormatException,
    WeakPasswordException,
)
from config import settings
from constants.regex import EMAIL_REGEX, FIRST_NAME_REGEX, PHONE_REGEX
from core.auth import access, refresh
from core.db import async_session, redis
from core.types import RoleType
from core.utils import strong_password
from core.utils.celery_worker import celery_app

async def create_tokens(user_id: str, client_slug: str) -> dict[str, str]:
    """
    Create access-token and refresh-token for a user.

    Args:
        user_id:
        client_slug:
    :return: A dictionary containing access-token and refresh-token.
    """
    access_token = access.encode(
        payload={"id": str(user_id), "client_id": client_slug}, expire_period=int(settings.ACCESS_TOKEN_EXP)
    )
    refresh_token = refresh.encode(
        payload={"id": str(user_id), "client_id": client_slug}, expire_period=int(settings.REFRESH_TOKEN_EXP)
    )

    return {"access_token": access_token, "refresh_token": refresh_token}


def validate_string_fields(values) -> dict:
    """
    Validate string fields for empty strings.
    :param values: Values to be validated.
    :return: Received values.
    """
    for field_name, value in values.items():
        if isinstance(value, str) and not value.strip():
            raise EmptyDescriptionException(
                message=f"{field_name} must not be an empty string"
            )
    return values


async def decrypt(
    rsa_key: rsa.RSAPrivateKey,
    enc_data: str,
    encrypt_key: str,
    iv_input: str,
    time_check: bool = False,
    timeout: int = 5,
) -> bytes:
    """Decrypts the given encrypted data.

    :param enc_data: Encrypted Data
    :param encrypt_key: Encrypted Key
    :param iv_input: IV Input
    :param time_check: Whether to check the time of the encrypted data
    :param timeout: Timeout in seconds(5 by default)
    :return: Decrypted code
    """
    try:
        code_bytes = encrypt_key.encode("UTF-8")
        encoded_by = base64.b64decode(code_bytes)
        decrypted_key = rsa_key.decrypt(encoded_by, asym_padding.PKCS1v15()).decode()

        iv = base64.b64decode(iv_input)
        enc = base64.b64decode(enc_data)
        cipher = Cipher(
            algorithms.AES(decrypted_key.encode("utf-8")),
            modes.CBC(iv),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(enc) + decryptor.finalize()
        unpadder = crypto_padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        payload = json.loads(plaintext.decode())
        if time_check:
            exp = datetime.fromisoformat(payload.get("timestamp"))
            if exp is None:
                raise InvalidEncryptedData
            current_time = datetime.now(timezone.utc)
            if (current_time - exp) > timedelta(seconds=timeout):
                raise InvalidEncryptedData
        return plaintext
    except Exception:
        raise InvalidEncryptedData








CIPHER = Fernet(settings.ENCRYPTION_KEY or "")


async def decryption(data: str) -> dict:
    """Decrypts the given encrypted data.

    :param: config
    :return: Decrypted codeS
    """
    decrypted_data = CIPHER.decrypt(data.encode("utf-8"))
    return json.loads(decrypted_data)


async def encryption(data: str) -> str:
    """Encrypts the given data.

    :param: data
    :return: Encrypted code
    """
    encrypted_data = CIPHER.encrypt(data.encode("utf-8"))
    return encrypted_data.decode("utf-8")


async def get_tenant_data(tenant_id: str):
    """Get the tenant data from the database."""
    async with async_session() as session:
        async with session.begin():
            tenant_data = await session.scalar(
                select(Tenant).where(Tenant.id == tenant_id)
            )
            return tenant_data


async def get_last_execution_date(mail_box_config_id: str) -> datetime | None | int:
    """Get the latest id from the database.
    :return: int
    """
    async with async_session() as session:
        async with session.begin():
            emails = await session.scalar(
                select(MicrosoftMailBoxConfig).where(
                    MicrosoftMailBoxConfig.id == mail_box_config_id
                )
            )
            if emails is None:
                return 0
            last_execution = emails.last_execution

    return last_execution


async def fetch_outlook_settings():
    """Fetch outlook settings from the database.
    :return:
    """
    async with async_session() as session:
        async with session.begin():
            result = await session.scalar(
                select(MicrosoftCredentialsConfig.config)
            )
            result = await decryption(result)

            client_id = result.get("client_id")
            redirect_uri = result.get("redirect_uri")
            client_secret = result.get("client_secret")
            refresh_token_validity_days = result.get("refresh_token_validity_days")

        return (
            client_id,
            redirect_uri,
            client_secret,
            refresh_token_validity_days,
        )


def capture_exception(e: Exception) -> None:
    """Captures the exception and sends it to Sentry."""
    if settings.ACTIVATE_WORKER_SENTRY is True:
        sentry_sdk.capture_exception(e)


async def fetch_mail_box_config(mail_box_config_id) -> MicrosoftMailBoxConfig:
    """Fetch user configuration from the database.
    :param mail_box_config_id: ID of the user
    :return: MicrosoftMailBoxConfig or None
    """
    async with async_session() as session:
        async with session.begin():
            result = await session.scalar(
                select(MicrosoftMailBoxConfig).where(
                    MicrosoftMailBoxConfig.id == mail_box_config_id
                )
            )
    return result


def compute_batch_size(cols: int) -> int:
    """
    Compute the batch size for a given number of columns.
    :param cols: The number of columns.
    :return: The batch size.
    """
    MAX_PARAMS = constants.MAX_PARAMS
    SAFETY = constants.SAFETY
    return max(1, min(constants.MAX_BATCH_SIZE, (MAX_PARAMS - SAFETY) // max(1, cols)))

async def revoke_running_task(mail_box_config_id: str) -> None:
    """Revokes a running Celery task associated with the given bank ID."""
    running_task_id = await redis.get(mail_box_config_id)
    if running_task_id is not None:
        celery_app.control.revoke(
            running_task_id, terminate=True, signal=constants.SIGKILL
        )
