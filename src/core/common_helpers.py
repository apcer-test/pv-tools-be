import base64
import re
import secrets
from uuid import UUID

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as crypto_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from pydantic import EmailStr
import sentry_sdk
from sqlalchemy import select

import constants
from apps.user.exceptions import (
    EmptyDescriptionException,
    InvalidEmailException,
    InvalidEncryptedData,
    InvalidPhoneFormatException,
    WeakPasswordException,
)
from config import settings
from constants.regex import EMAIL_REGEX, FIRST_NAME_REGEX, PHONE_REGEX
from core.auth import access, admin_access, admin_refresh, refresh
from core.exceptions import InvalidRoleException
from core.types import RoleType
from core.utils import strong_password
from datetime import datetime, timedelta,timezone
import json

from core.db import async_session
from apps.mail_box_config.models.mail_box import MicrosoftMailBoxConfig
from apps.tenant.models.models import Tenant
from apps.mail_box_config.models.credentials import MicrosoftCredentialsConfig


async def create_password():
    """
    Create a random password.

    :return: A randomly generated password.
    """
    return secrets.token_urlsafe(15)


async def create_tokens(user_id: UUID, role: RoleType) -> dict[str, str]:
    """
    Create access-token and refresh-token for a user.

    Args:
        role:
        user_id:
    :return: A dictionary containing access-token and refresh-token.
    """
    if role == RoleType.USER:
        access_token = access.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.ACCESS_TOKEN_EXP)
        )
        refresh_token = refresh.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.REFRESH_TOKEN_EXP)
        )
    elif role == RoleType.ADMIN:
        access_token = admin_access.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.ACCESS_TOKEN_EXP)
        )
        refresh_token = admin_refresh.encode(
            payload={"id": str(user_id)}, expire_period=int(settings.REFRESH_TOKEN_EXP)
        )
    else:
        raise InvalidRoleException

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
    rsa_key: rsa.RSAPrivateKey, enc_data: str, encrypt_key: str, iv_input: str, time_check: bool = False, timeout: int = 5
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
        decrypted_key = rsa_key.decrypt(
            encoded_by,
            asym_padding.PKCS1v15()
        ).decode()

        iv = base64.b64decode(iv_input)
        enc = base64.b64decode(enc_data)
        cipher = Cipher(
            algorithms.AES(decrypted_key.encode("utf-8")),
            modes.CBC(iv),
            backend=default_backend()
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


def validate_input_fields(
    first_name: str, email: EmailStr, phone: str, password: str
) -> None:
    """
    Validate email, phone, and password fields.

    Args:
        first_name (str): The user's first name.
        email (EmailStr): The user's email address.
        phone (str): The user's phone number.
        password (str): The user's password.

    Raises:
        ValueError: If any of the fields are invalid.
    """

    if not re.match(EMAIL_REGEX, email):
        raise InvalidEmailException

    if not re.search(FIRST_NAME_REGEX, first_name, re.I):
        raise ValueError(constants.INVALID + f"{first_name.replace('_', ' ')}")

    if not re.match(PHONE_REGEX, phone, re.I):
        raise InvalidPhoneFormatException

    if not strong_password(password):
        raise WeakPasswordException


def validate_email(email: str) -> str | None:
    """
    Validate the format of an email address.
    :param email: The email address to be validated.
    :return: The validated email address.
    """

    if not re.match(constants.EMAIL_REGEX, email):
        raise InvalidEmailException

    if not isinstance(email, str) and email is not None:
        raise InvalidEmailException

    return email

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

async def fetch_outlook_settings(tenant_id: str):
    """:param tenant_id:
    :return:
    """
    async with async_session() as session:
        async with session.begin():
            result = await session.scalar(
                select(MicrosoftCredentialsConfig.config).where(
                    MicrosoftCredentialsConfig.tenant_id == tenant_id
                )
            )
            result = await decryption(result)

            client_id = result.get("client_id")
            redirect_uri = result.get("redirect_uri")
            client_secret = result.get("client_secret")
            refresh_token_validity_days = result.get(
                "refresh_token_validity_days"
            )
            microsoft_tenant_id = result.get("tenant_id")

        return (
            client_id,
            redirect_uri,
            client_secret,
            refresh_token_validity_days,
            microsoft_tenant_id,
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
                select(MicrosoftMailBoxConfig)
                .where(MicrosoftMailBoxConfig.id == mail_box_config_id)
            )
    return result