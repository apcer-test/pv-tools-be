from typing import TYPE_CHECKING
from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.clients.models.clients import Clients
    from apps.users.models.user import Users


class UserType(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing UserType information.

    Attributes:
        name (str): The user's type name.
        slug (str): The user's type slug.
        description (str): The user's type description.
        meta_data (dict): The user's type metadata.
        client_id (str): The client id.
    """

    __tablename__ = "user_type"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id", use_alter=True, ondelete="CASCADE"), nullable=False)

    client: Mapped["Clients"] = relationship(
        "Clients", back_populates="user_types", foreign_keys=[client_id]
    )

    users: Mapped[list["Users"]] = relationship(
        "Users", back_populates="user_type", foreign_keys="[Users.user_type_id]"
    )

    # Unique constraint for name and client_id combination
    __table_args__ = (
        UniqueConstraint("name", "client_id", name="uq_name_client_id"),
    )
