from typing import TYPE_CHECKING
from typing import List
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.media.models.media import Media
    from apps.user_type.models.user_type import UserType
    from apps.roles.models.roles import Roles
    from apps.modules.models.modules import Modules
    from apps.permissions.models.permissions import Permissions
    from apps.users.models.user import Users
    from apps.users.models.user import UserRoleLink

class Clients(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Represents a Client in the system.

    Attributes:
        name (str): The name of the client.
        code (str): The code of the client.
        slug (str): The slug of the client.
        description (str): The description of the client. Can be null.
        meta_data (dict): The metadata of the client. Can be null.
        media_id (str): The media id of the client. Can be null.
        is_active (bool): Whether the client is active. Default is True.
    """

    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    media_id: Mapped[str | None] = mapped_column(ForeignKey("media.id", use_alter=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    media: Mapped["Media"] = relationship(
        "Media", back_populates="clients", foreign_keys=[media_id]
    )

    user_types: Mapped[List["UserType"]] = relationship(
        "UserType", back_populates="client", cascade="all, delete-orphan"
    )

    roles: Mapped[List["Roles"]] = relationship(
        "Roles", back_populates="client", cascade="all, delete-orphan"
    )

    modules: Mapped[List["Modules"]] = relationship(
        "Modules", back_populates="client", cascade="all, delete-orphan"
    )

    permissions: Mapped[List["Permissions"]] = relationship(
        "Permissions", back_populates="client", cascade="all, delete-orphan"
    )

    users: Mapped[List["Users"]] = relationship(
        secondary="user_role_link",
        primaryjoin="Clients.id == UserRoleLink.client_id",
        secondaryjoin="UserRoleLink.user_id == Users.id",
        viewonly=True,
    )

    user_role_links: Mapped[List["UserRoleLink"]] = relationship(
        "UserRoleLink", back_populates="client", foreign_keys="[UserRoleLink.client_id]"
    )
