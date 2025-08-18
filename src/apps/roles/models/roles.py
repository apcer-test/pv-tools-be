from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.modules.models.modules import Modules
    from apps.users.models.user import UserRoleLink
    from apps.permissions.models.permissions import Permissions

class Roles(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing Role information.

    Attributes:
        name (str): The role's name.
        slug (str): The role's slug.
        description (str): The role's description.
        meta_data (dict): The role's metadata.
        modules (list): The modules associated with the role.
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=True)

    modules: Mapped[list["Modules"]] = relationship(
        secondary="role_module_permission_link",
        primaryjoin="Roles.id == RoleModulePermissionLink.role_id",
        secondaryjoin="RoleModulePermissionLink.module_id == Modules.id",
    )

    user_role_links: Mapped[list["UserRoleLink"]] = relationship(
        "UserRoleLink", back_populates="role", foreign_keys="[UserRoleLink.role_id]"
    )

    role_module_permission_links: Mapped[list["RoleModulePermissionLink"]] = relationship(
        "RoleModulePermissionLink", back_populates="role", foreign_keys="[RoleModulePermissionLink.role_id]"
    )


class RoleModulePermissionLink(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing RoleModulePermissionLink information.

    Attributes:
        role_id (str): The role id.
        module_id (str): The module id.
        permission_id (str): The permission id.
    """

    __tablename__ = "role_module_permission_link"

    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), nullable=False)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id"), nullable=False)
    permission_id: Mapped[str] = mapped_column(ForeignKey("permissions.id"), nullable=False)

    # Relationships
    role: Mapped["Roles"] = relationship(
        "Roles", back_populates="role_module_permission_links", foreign_keys=[role_id]
    )
    module: Mapped["Modules"] = relationship(
        "Modules", back_populates="role_module_permission_links", foreign_keys=[module_id]
    )
    permission: Mapped["Permissions"] = relationship(
        "Permissions", back_populates="role_module_permission_links", foreign_keys=[permission_id]
    )
