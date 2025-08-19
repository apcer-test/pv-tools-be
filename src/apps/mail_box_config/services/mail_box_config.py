from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from ulid import ULID

from apps.clients.models.clients import Clients
from apps.mail_box_config.exceptions import (
    ClientNotFoundException,
    MailBoxAlreadyConfigured,
    MailBoxConfigNotFound,
)
from apps.mail_box_config.helper import revoke_running_task
from apps.mail_box_config.models.mail_box import MicrosoftMailBoxConfig
from core.common_helpers import fetch_outlook_settings
from core.db import db_session, redis
from core.types import FrequencyType, Providers
from core.utils.celery_worker import pooling_mail_box
from core.utils.microsoft_oauth_util import generate_refresh_token


class MailBoxService:
    """Service with methods to set and get values."""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """Call method to inject db_session as a dependency.
        This method also calls a database connection which is injected here.

        :param session: an asynchronous database connection
        """
        self.session = session

    async def add_mail_box_config(
        self,
        client_id: str,
        recipient_email: str,
        app_password: str,
        provider: Providers,
        frequency: FrequencyType,
    ) -> MicrosoftMailBoxConfig:
        """This method adds mail box configuration to the database."""
        token_expiry = None

        client = await self.session.scalar(
            select(Clients).where(Clients.id == client_id)
        )
        if not client:
            raise ClientNotFoundException

        get_email = await self.session.scalar(
            select(MicrosoftMailBoxConfig).where(
                MicrosoftMailBoxConfig.recipient_email == recipient_email
            )
        )
        if get_email:
            raise MailBoxAlreadyConfigured

        if provider == Providers.MICROSOFT and app_password:
            (
                microsoft_client_id,
                redirect_uri,
                client_secret,
                refresh_token_validity_days,
            ) = await fetch_outlook_settings()
            app_password = await generate_refresh_token(
                app_password,
                microsoft_client_id,
                redirect_uri,
                client_secret,
                refresh_token_validity_days,
            )
            token_expiry = datetime.now() + timedelta(int(refresh_token_validity_days))

            mail_box_config = MicrosoftMailBoxConfig.create(
                client_id=client_id,
                recipient_email=recipient_email,
                app_password=app_password,
                provider=provider,
                frequency=frequency,
                app_password_expired_at=token_expiry,
                is_active=True,
            )
            self.session.add(mail_box_config)

            # Start polling immediately after configuration
            await revoke_running_task(mail_box_config.id)
            task_id = str(ULID())
            await redis.set(name=str(mail_box_config.id), value=task_id)

            # Schedule task to start after DB transaction completes
            pooling_mail_box.apply_async(
                eta=datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=5),
                task_id=task_id,
                args=[str(mail_box_config.id), frequency],
            )
            return mail_box_config

    async def get_mail_box_config(
        self, mail_box_config_id: str, client_id: str
    ) -> MicrosoftMailBoxConfig | dict:
        """Get the configuration for the user"""
        mail_box_config = await self.session.scalar(
            select(MicrosoftMailBoxConfig)
            .options(
                load_only(
                    MicrosoftMailBoxConfig.recipient_email,
                    MicrosoftMailBoxConfig.app_password,
                    MicrosoftMailBoxConfig.app_password_expired_at,
                    MicrosoftMailBoxConfig.provider,
                    MicrosoftMailBoxConfig.frequency,
                    MicrosoftMailBoxConfig.last_execution,
                    MicrosoftMailBoxConfig.is_active,
                )
            )
            .where(
                MicrosoftMailBoxConfig.id == mail_box_config_id,
                MicrosoftMailBoxConfig.client_id == client_id,
            )
        )
        if not mail_box_config:
            raise MailBoxConfigNotFound

        return mail_box_config

    async def get_mail_box_config_list(
        self, client_id: str, page_params: Params
    ) -> list[MicrosoftMailBoxConfig]:
        """Get the list of mail box configurations for the client"""
        query = (
            select(MicrosoftMailBoxConfig)
            .where(MicrosoftMailBoxConfig.client_id == client_id)
            .order_by(MicrosoftMailBoxConfig.updated_at.desc())
        )
        return await paginate(self.session, query, page_params)

    async def update_mail_box_config(
        self,
        mail_box_config_id: str,
        client_id: str,
        recipient_email: str | None = None,
        app_password: str | None = None,
        provider: Providers | None = None,
        frequency: FrequencyType | None = None,
        reason: str | None = None,
    ):
        """Update the configuration for the user"""
        mail_box_config = await self.session.scalar(
            select(MicrosoftMailBoxConfig).where(
                MicrosoftMailBoxConfig.client_id == client_id,
                MicrosoftMailBoxConfig.id == mail_box_config_id,
            )
        )
        if not mail_box_config:
            raise MailBoxConfigNotFound

        reschedule_task = False

        if recipient_email:
            mail_box_config.recipient_email = recipient_email

        if app_password:
            (client_id, redirect_uri, client_secret, refresh_token_validity_days) = (
                await fetch_outlook_settings()
            )

            app_password = await generate_refresh_token(
                app_password,
                client_id,
                redirect_uri,
                client_secret,
                refresh_token_validity_days,
            )
            refresh_token_exp = datetime.now(UTC).replace(tzinfo=None) + timedelta(
                days=float(refresh_token_validity_days)  # type: ignore
            )

            mail_box_config.app_password = app_password
            mail_box_config.app_password_expired_at = refresh_token_exp

        if provider:
            mail_box_config.provider = provider

        if frequency:
            if mail_box_config.frequency != frequency:
                mail_box_config.frequency = frequency
                reschedule_task = True

        if reschedule_task:
            await revoke_running_task(mail_box_config.id)
            task_id = str(ULID())
            await redis.set(name=str(mail_box_config.id), value=task_id)

            # Schedule task to start after DB transaction completes
            pooling_mail_box.apply_async(
                eta=datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=10),
                task_id=task_id,
                args=[str(mail_box_config.id), frequency],
            )
        print(f"reason: {reason}")

        return mail_box_config

    async def update_mail_box_config_status(
        self, mail_box_config_id: str, client_id: str
    ):
        """
        Toggle the is_active status of the mail box configuration.
        Instead of using a value from the request body, this method
        sets is_active to the opposite of its current value in the database.
        """
        mail_box_config = await self.session.scalar(
            select(MicrosoftMailBoxConfig).where(
                MicrosoftMailBoxConfig.client_id == client_id,
                MicrosoftMailBoxConfig.id == mail_box_config_id,
            )
        )
        if not mail_box_config:
            raise MailBoxConfigNotFound
        # Toggle the is_active status
        mail_box_config.is_active = not mail_box_config.is_active
        return mail_box_config
