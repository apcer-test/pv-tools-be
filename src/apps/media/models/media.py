from typing import TYPE_CHECKING, List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.clients.models.clients import Clients


class Media(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing Media information.

    Attributes:
        file_name (str): The name of the media, e.g. profile.jpg.
        file_path (str): The path of the media, S3 URL.
        file_type (str): The type of the media, e.g. image, document or unknown.
    """

    __tablename__ = "media"

    file_name: Mapped[str] = mapped_column(String(128), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)

    clients: Mapped[List["Clients"]] = relationship(
        "Clients", back_populates="media", cascade="all, delete-orphan"
    )