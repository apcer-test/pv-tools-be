import imaplib
from datetime import UTC, date, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from ulid import ULID

import constants
from apps.mail_box_config.exceptions import (
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
from core.utils.schema import SuccessResponse


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
        tenant_id: str,
        recipient_email: str,
        app_password: str,
        provider: Providers,
        frequency: FrequencyType,
        start_date: date,
        end_date: date,
        company_emails: list[str] = [],
        subject_lines: list[str] = [],
    ) -> MicrosoftMailBoxConfig:
        """This method adds mail box configuration to the database."""
        token_expiry = None

        get_email = await self.session.scalar(
            select(MicrosoftMailBoxConfig).where(
                MicrosoftMailBoxConfig.recipient_email == recipient_email
            )
        )
        if get_email:
            raise MailBoxAlreadyConfigured

        if provider == Providers.MICROSOFT and app_password:

            (
                client_id,
                redirect_uri,
                client_secret,
                refresh_token_validity_days,
                microsoft_tenant_id,
            ) = await fetch_outlook_settings(tenant_id=tenant_id)
            app_password = await generate_refresh_token(
                app_password,
                client_id,
                redirect_uri,
                client_secret,
                refresh_token_validity_days,
                microsoft_tenant_id,
            )
            token_expiry = datetime.now() + timedelta(int(refresh_token_validity_days))

            mail_box_config = MicrosoftMailBoxConfig.create(
                tenant_id=tenant_id,
                recipient_email=recipient_email,
                app_password=app_password,
                provider=provider,
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                app_password_expired_at=token_expiry,
                company_emails=company_emails,
                subject_lines=subject_lines,
            )
            self.session.add(mail_box_config)

            if start_date:
                if mail_box_config.start_date == start_date:
                    mail_box_config.start_date = start_date
                    await revoke_running_task(mail_box_config.id)
                    task_id = str(ULID())
                    await redis.set(name=str(mail_box_config.id), value=task_id)
                    current_date_time = datetime.now(UTC).replace(tzinfo=None)
                    if start_date == current_date_time.date():
                        eta = current_date_time + timedelta(seconds=5)

                    else:
                        current_date_time = datetime.now(UTC).replace(tzinfo=None)
                        start_date_datetime = datetime(
                            year=start_date.year,
                            month=start_date.month,
                            day=start_date.day,
                            hour=current_date_time.hour,
                            minute=current_date_time.minute,
                            second=current_date_time.second,
                            tzinfo=None,
                        )
                        eta = start_date_datetime
                    additional_filter = None
                    pooling_mail_box.apply_async(
                        eta=eta,
                        task_id=task_id,
                        args=[mail_box_config.id, frequency, additional_filter],
                    )
            return mail_box_config

    async def get_mail_box_config(
        self, mail_box_config_id: UUID, tenant_id: UUID
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
                    MicrosoftMailBoxConfig.start_date,
                    MicrosoftMailBoxConfig.end_date,
                    MicrosoftMailBoxConfig.frequency,
                    MicrosoftMailBoxConfig.company_emails,
                    MicrosoftMailBoxConfig.subject_lines,
                )
            )
            .where(
                MicrosoftMailBoxConfig.id == mail_box_config_id,
                MicrosoftMailBoxConfig.tenant_id == tenant_id,
            )
        )
        if not mail_box_config:
            raise MailBoxConfigNotFound

        return mail_box_config

    async def get_mail_box_config_list(
        self, tenant_id: UUID, page_params: Params
    ) -> list[MicrosoftMailBoxConfig]:
        query = (
            select(MicrosoftMailBoxConfig)
            .where(MicrosoftMailBoxConfig.tenant_id == tenant_id)
            .order_by(MicrosoftMailBoxConfig.updated_at.desc())
        )
        return await paginate(self.session, query, page_params)

    async def update_mail_box_config(
        self,
        mail_box_config_id: UUID,
        tenant_id: UUID,
        app_password: str | None = None,
        provider: Providers | None = None,
        frequency: FrequencyType | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        company_emails: list[str] = [],
        subject_lines: list[str] = [],
    ):
        """Update the configuration for the user"""
        mail_box_config = await self.session.scalar(
            select(MicrosoftMailBoxConfig).where(
                MicrosoftMailBoxConfig.tenant_id == tenant_id,
                MicrosoftMailBoxConfig.id == mail_box_config_id,
            )
        )
        if not mail_box_config:
            raise MailBoxConfigNotFound

        reschedule_task = False

        if app_password:
            (
                client_id,
                redirect_uri,
                client_secret,
                refresh_token_validity_days,
                microsoft_tenant_id,
            ) = await fetch_outlook_settings(tenant_id=tenant_id)

            app_password = await generate_refresh_token(
                app_password,
                client_id,
                redirect_uri,
                client_secret,
                refresh_token_validity_days,
                microsoft_tenant_id,
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

        if start_date:
            if mail_box_config.start_date != start_date:
                mail_box_config.start_date = start_date
                reschedule_task = True

        if end_date:
            if mail_box_config.end_date != end_date:
                mail_box_config.end_date = end_date

        if company_emails:
            mail_box_config.company_emails = company_emails

        if subject_lines:
            mail_box_config.subject_lines = subject_lines

        if reschedule_task:
            await revoke_running_task(mail_box_config.id)
            task_id = str(uuid4())
            await redis.set(name=str(mail_box_config.id), value=task_id)

            now = datetime.now(UTC).replace(tzinfo=None)
            if start_date is None:
                start_date = mail_box_config.start_date
            if start_date <= now.date():
                eta = now + timedelta(seconds=5)
            else:
                eta = datetime(
                    year=start_date.year if start_date else mail_box_config.start_date,
                    month=(
                        start_date.month if start_date else mail_box_config.start_date
                    ),
                    day=start_date.day if start_date else mail_box_config.start_date,
                    hour=now.hour,
                    minute=now.minute,
                    second=now.second,
                    tzinfo=None,
                )
            additional_filter = None
            pooling_mail_box.apply_async(
                eta=eta,
                task_id=task_id,
                args=[mail_box_config.id, frequency, additional_filter],
            )

        return mail_box_config

    async def delete_mail_box_config(self, tenant_id: UUID, mail_box_config_id: UUID):
        mail_box_config = await self.session.scalar(
            select(MicrosoftMailBoxConfig).where(
                MicrosoftMailBoxConfig.tenant_id == tenant_id,
                MicrosoftMailBoxConfig.id == mail_box_config_id,
            )
        )
        if not mail_box_config:
            raise MailBoxConfigNotFound
        await revoke_running_task(mail_box_config_id)
        await self.session.delete(mail_box_config)
        return SuccessResponse
