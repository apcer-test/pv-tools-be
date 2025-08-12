from typing import TYPE_CHECKING, Self

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ulid import ULID

from core.db import Base
from core.types import RoleType
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.users.models.user import Users


class Tenant(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for Tenant Lookups."""

    __tablename__ = "tenant"

    secret_key: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True, server_default="True")

    users: Mapped[list["Users"]] = relationship(
        "Users",
        secondary="tenant_users",
        back_populates="tenants",
        primaryjoin="Tenant.id == TenantUsers.tenant_id",
        secondaryjoin="TenantUsers.user_id == Users.id",
        viewonly=True,
    )

    tenant_users: Mapped[list["TenantUsers"]] = relationship(
        "TenantUsers",
        back_populates="tenant",
        primaryjoin="Tenant.id == TenantUsers.tenant_id",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        """:return: A string representation of the Tenant Lookup entry."""
        return f"<Tenant id={self.id} secret_key={self.secret_key}>"

    @classmethod
    def create(cls, secret_key: str, is_active: bool = True) -> Self:
        """Create a tenant lookup entry.

        :param secret_key: The secret key associated with the tenant.

        :return: An instance of TenantLookups.
        """
        return cls(id=str(ULID()), secret_key=secret_key, is_active=is_active)


class TenantUsers(Base, TimeStampMixin, UserMixin):
    """Pivot table model for User-Tenant relationships with roles.
    This table manages the association between users and tenants along with their roles.
    """

    __tablename__ = "tenant_users"
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenant.id", ondelete="cascade"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="cascade"), primary_key=True
    )
    role: Mapped[str] = mapped_column()

    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="tenant_users", foreign_keys="[TenantUsers.tenant_id]"
    )
    user: Mapped["Users"] = relationship(
        "Users", back_populates="tenant_users", foreign_keys="[TenantUsers.user_id]"
    )

    def __str__(self) -> str:
        """:return: A string representation of the User-Tenant-Role relationship."""
        return f"<TenantUsers tenant_id={self.tenant_id} user_id={self.user_id} role={self.role}>"

    @classmethod
    def create(cls, tenant_id: str, user_id: str, role: str = RoleType.ADMIN) -> Self:
        """Create a user-tenant role relationship.

        :param tenant_id: The ID of the tenant
        :param user_id: The ID of the user
        :param role: The role of the user in the tenant (defaults to admin)
        :return: An instance of UserTenantRole
        """
        return cls(tenant_id=tenant_id, user_id=user_id, role=role)
