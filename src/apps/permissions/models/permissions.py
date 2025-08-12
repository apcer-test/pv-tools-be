"""Model for representing permission information."""

from typing import TYPE_CHECKING
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.clients.models.clients import Clients
    from apps.roles.models.roles import RoleModulePermissionLink
    from apps.modules.models.modules import ModulePermissionLink

class Permissions(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing permission information.

    Attributes:
        name (str): The permission name.
        slug (str): The permission slug.
        description (str): The permission description.
        meta_data (dict): The permission metadata.
        client_id (str): The client id.
        client (Client): The client.
    """

    __tablename__ = "permissions"

    # Columns
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Foreign keys
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    client: Mapped["Clients"] = relationship(
        "Clients", back_populates="permissions", foreign_keys=[client_id]
    )

    role_module_permission_links: Mapped[list["RoleModulePermissionLink"]] = relationship(
        "RoleModulePermissionLink", back_populates="permission", foreign_keys="[RoleModulePermissionLink.permission_id]"
    )

    module_permission_links: Mapped[list["ModulePermissionLink"]] = relationship(
        "ModulePermissionLink", back_populates="permission", foreign_keys="[ModulePermissionLink.permission_id]"
    )