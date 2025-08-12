"""Model for representing modules information."""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.permissions.models.permissions import Permissions
    from apps.clients.models.clients import Clients
    from apps.roles.models.roles import RoleModulePermissionLink

class Modules(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing modules information.

    Attributes:
        name (str): The module name.
        slug (str): The module slug.
        description (str): The module description.
        meta_data (dict): The module metadata.
        client_id (str): The client id.
        parent_module_id (str): The parent module id.
        child_modules (list): The child modules.
        permissions (list): The permissions.
    """

    __tablename__ = "modules"

    # Columns
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    client: Mapped["Clients"] = relationship(
        "Clients", back_populates="modules", foreign_keys=[client_id]
    )

    # Relationships
    parent_module_id: Mapped[str] = mapped_column(
        ForeignKey("modules.id"), nullable=True
    )
    parent_module: Mapped["Modules"] = relationship(
        primaryjoin="Modules.parent_module_id == Modules.id",
        remote_side="Modules.id",
        back_populates="child_modules",
    )
    child_modules: Mapped[list["Modules"]] = relationship(
        primaryjoin="Modules.id == Modules.parent_module_id",
        remote_side="Modules.parent_module_id",
        back_populates="parent_module",
    )
    permissions: Mapped[list["Permissions"]] = relationship(
        secondary="module_permission_link",
        primaryjoin="and_(Modules.id==ModulePermissionLink.module_id, ModulePermissionLink.deleted_at==None)",
        secondaryjoin="ModulePermissionLink.permission_id == Permissions.id",
    )

    role_module_permission_links: Mapped[list["RoleModulePermissionLink"]] = relationship(
        "RoleModulePermissionLink", back_populates="module", foreign_keys="[RoleModulePermissionLink.module_id]"
    )

    module_permission_links: Mapped[list["ModulePermissionLink"]] = relationship(
        "ModulePermissionLink", back_populates="module", foreign_keys="[ModulePermissionLink.module_id]"
    )


class ModulePermissionLink(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing permissions of module."""

    __tablename__ = "module_permission_link"

    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id"), nullable=False)
    permission_id: Mapped[str] = mapped_column(ForeignKey("permissions.id"), nullable=False)

    # Relationships
    module: Mapped["Modules"] = relationship(
        "Modules", back_populates="module_permission_links", foreign_keys=[module_id]
    )
    permission: Mapped["Permissions"] = relationship(
        "Permissions", back_populates="module_permission_links", foreign_keys=[permission_id]
    )
