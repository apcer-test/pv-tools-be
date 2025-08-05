from datetime import date, datetime
from typing import Self

from sqlalchemy import ARRAY, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from core.db import Base
from core.types import FrequencyType, Providers
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin


class MicrosoftMailBoxConfig(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing microsoft mail box configuration information."""

    __tablename__ = "microsoft_mail_box_config"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id", ondelete="cascade"))
    recipient_email: Mapped[str] = mapped_column()
    app_password: Mapped[str] = mapped_column()
    provider: Mapped[str] = mapped_column()
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date] = mapped_column()
    frequency: Mapped[str] = mapped_column()
    app_password_expired_at: Mapped[datetime] = mapped_column(nullable=True)
    company_emails: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    subject_lines: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    last_execution: Mapped[datetime] = mapped_column(nullable=True)

    @classmethod
    def create(
        cls,
        tenant_id: str,
        recipient_email: str,
        app_password: str,
        provider: Providers,
        start_date: date,
        end_date: date,
        frequency: FrequencyType,
        app_password_expired_at: datetime,
        company_emails: list[str] = [],
        subject_lines: list[str] = [],
    ):
        return cls(
            id=str(ULID()),
            tenant_id=tenant_id,
            recipient_email=recipient_email,
            app_password=app_password,
            provider=provider,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            app_password_expired_at=app_password_expired_at,
            company_emails=company_emails,
            subject_lines=subject_lines,
        )
