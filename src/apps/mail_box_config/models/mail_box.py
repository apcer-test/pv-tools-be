from datetime import date, datetime
from typing import TYPE_CHECKING, Self

from sqlalchemy import ARRAY, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ulid import ULID

from core.db import Base
from core.types import FrequencyType, Providers
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.clients.models.clients import Clients


class MicrosoftMailBoxConfig(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing microsoft mail box configuration information."""

    __tablename__ = "microsoft_mail_box_config"
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id", ondelete="cascade"))
    recipient_email: Mapped[str] = mapped_column()
    app_password: Mapped[str] = mapped_column()
    provider: Mapped[str] = mapped_column()
    frequency: Mapped[str] = mapped_column()
    app_password_expired_at: Mapped[datetime] = mapped_column(nullable=True)
    last_execution: Mapped[datetime] = mapped_column(nullable=True)

    # Relationships
    client: Mapped["Clients"] = relationship(
        "Clients", back_populates="microsoft_mail_box_configs"
    )

    @classmethod
    def create(
        cls,
        client_id: str,
        recipient_email: str,
        app_password: str,
        provider: Providers,
        frequency: FrequencyType,
        app_password_expired_at: datetime,
    ) -> Self:
        """Create a new mail box configuration"""
        return cls(
            id=str(ULID()),
            client_id=client_id,
            recipient_email=recipient_email,
            app_password=app_password,
            provider=provider,
            frequency=frequency,
            app_password_expired_at=app_password_expired_at,
            last_execution=None,
        )
