from typing import Self

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin


class MicrosoftCredentialsConfig(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """
    Model for storing microsoft credentials.
    """

    __tablename__ = "microsoft_credentials_config"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id", ondelete="cascade"))
    config: Mapped[str | None] = mapped_column()

    def __str__(self) -> str:
        """:return:"""
        return f"<MicrosoftCredentialsConfig>"

    @classmethod
    def create(cls, tenant_id: str, config: str | bytes | None = None) -> Self:
        """Create a microsoft credentials entry.

        Args:
            config: Dictionary containing microsoft credentials

        Returns:
            MicrosoftCredentialsConfig instance
        """
        return cls(id=str(ULID()), tenant_id=tenant_id, config=config)
