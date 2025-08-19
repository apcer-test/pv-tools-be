import json
from copy import deepcopy
from typing import Annotated

from cryptography.fernet import Fernet
from fastapi import Depends
from fastapi import Request as FastAPIRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from apps.mail_box_config.models import MicrosoftCredentialsConfig
from config import settings
from core.common_helpers import decrypt
from core.db import db_session


class MicrosoftCredentialsService:
    """A service class for managing microsoft credentials."""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Initialize AuthService with a database session
        This method also calls a database connection which is injected here.

        Args:
            session (AsyncSession): An asynchronous database connection.
        """
        self.session = session
        key = settings.ENCRYPTION_KEY or ""
        self.cipher = Fernet(key.encode())

    def deep_merge(self, dict1, dict2):
        """Deep merge two dictionaries with special handling for certain fields.

        Args:
            dict1: The original dictionary
            dict2: The dictionary with updates to apply

        Returns:
            dict: The merged dictionary
        """
        result = deepcopy(dict1)

        for key, value in dict2.items():
            # If the key exists in both dictionaries
            if key in result:
                # If both values are dictionaries, recursively merge them
                if isinstance(value, dict) and isinstance(result[key], dict):
                    # Special handling for API headers - completely replace instead of merge
                    if key in [
                        "client_id",
                        "redirect_uri",
                        "client_secret",
                        "refresh_token_validity_days",
                        "microsoft_tenant_id",
                    ]:
                        result[key] = deepcopy(value)
                    else:
                        result[key] = self.deep_merge(result[key], value)
                else:
                    # For non-dict values, just use the new one
                    result[key] = deepcopy(value)
            else:
                # If the key doesn't exist in dict1, just add it
                result[key] = deepcopy(value)

        return result

    async def update_microsoft_credentials(
        self,
        request: FastAPIRequest,
        encrypted_data: str,
        encrypted_key: str,
        iv: str,
    ) -> dict:
        """Update microsoft credentials in the database.

        Args:
            request (FastAPIRequest): The incoming request object.
            encrypted_data (str): The encrypted data containing updated tenant settings.
            encrypted_key (str): The encrypted key used for decryption.
            iv_ (str): The initialization vector used for decryption.

        Returns:
            dict: Updated microsoft credentials.
        """
        decrypted_data = await decrypt(
            rsa_key=request.app.state.rsa_key,
            enc_data=encrypted_data,
            encrypt_key=encrypted_key,
            iv_input=iv,
        )
        new_settings_data = json.loads(decrypted_data)

        tenant_settings = await self.session.scalar(
            select(MicrosoftCredentialsConfig)
        )

        if not tenant_settings:
            encrypted_settings = self.cipher.encrypt(
                json.dumps(new_settings_data).encode("utf-8")
            ).decode("utf-8")

            tenant_settings = MicrosoftCredentialsConfig.create(
                config=encrypted_settings
            )
            self.session.add(tenant_settings)

            return new_settings_data

        current_settings = json.loads(
            self.cipher.decrypt(tenant_settings.config).decode("utf-8")
        )

        merged_settings = self.deep_merge(current_settings, new_settings_data)

        encrypted_updated_settings = self.cipher.encrypt(
            json.dumps(merged_settings).encode("utf-8")
        ).decode("utf-8")

        tenant_settings.config = encrypted_updated_settings
        flag_modified(tenant_settings, "config")

        return merged_settings

    async def get_microsoft_credentials(self) -> dict:
        """Retrieve tenant settings from the database.

        Args:
            tenant_id (UUID): The tenant's unique identifier.
            user_id (UUID): The user's unique identifier.

        Returns:
            dict: Tenant settings stored in the database.
        """
        tenant_settings = await self.session.scalar(
            select(MicrosoftCredentialsConfig)
        )
        if not tenant_settings:
            return {}
        settings_data = json.loads(
            self.cipher.decrypt(tenant_settings.config).decode("utf-8")
        )

        return settings_data
