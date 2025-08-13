from typing import TYPE_CHECKING, List

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.roles.models import Roles
    from apps.user_type.models.user_type import UserType
    from apps.clients.models.clients import Clients
    from apps.tenant.models.models import Tenant, TenantUsers

class Users(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing user information.

    Attributes:
        username (str): The user's username.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        email (str): The user's email address (unique).
        phone (str | None): The user's phone number (unique).
        user_type_id (str): The user's user_type_id.
        is_active (bool): The user's active status.
        reporting_manager_id (str | None): The user's reporting manager id.
        description (str | None): The user's description.
        meta_data (dict | None): The user's metadata.
        user_type (UserType): The user's user type.
        meta_data (dict | None): The user's metadata.
        is_active (bool): The user's active status.
        clients (list): The user's clients.
        roles (list): The user's roles.
        role_links (list): The user's role links.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(16), nullable=True)
    user_type_id: Mapped[str] = mapped_column(ForeignKey("user_type.id", use_alter=True, ondelete="CASCADE"), nullable=False)
    user_type: Mapped["UserType"] = relationship(
        "UserType", back_populates="users", foreign_keys=[user_type_id]
    )

    reporting_manager_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", use_alter=True, ondelete="SET NULL"), nullable=True)
    reporting_manager: Mapped["Users"] = relationship("Users", remote_side="[Users.id]", foreign_keys=[reporting_manager_id])
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="True")


    clients: Mapped[List["Clients"]] = relationship(
        secondary="user_role_link",
        primaryjoin="Users.id == UserRoleLink.user_id",
        secondaryjoin="UserRoleLink.client_id == Clients.id",
        viewonly=True,
    )

    role_links: Mapped[List["UserRoleLink"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        primaryjoin="Users.id == UserRoleLink.user_id",
    )

    roles: Mapped[List["Roles"]] = relationship(
        secondary="user_role_link",
        primaryjoin="Users.id == UserRoleLink.user_id",
        secondaryjoin="UserRoleLink.role_id == Roles.id",
        viewonly=True,
    )

    tenants: Mapped[List["Tenant"]] = relationship(
        "Tenant",
        secondary="tenant_users",
        back_populates="users",
        primaryjoin="Users.id == TenantUsers.user_id",
        secondaryjoin="TenantUsers.tenant_id == Tenant.id",
        viewonly=True,
    )

    tenant_users: Mapped[List["TenantUsers"]] = relationship(
        "TenantUsers",
        back_populates="user",
        primaryjoin="Users.id == TenantUsers.user_id",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        """
        Return a string representation of the user.

        :return: A string with the user's first and last name.
        """
        return f"<{self.first_name} {self.last_name}>"

    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        password: str,
        username: str = None,
        user_type_id: str = None,
        description: str = None,
        meta_data: dict = None,
        is_active: bool = True,
    ):
        """
        Create a new user.

        :param first_name: The user's first name.
        :param last_name: The user's last name.
        :param phone: The user's phone number.
        :param email: The user's email address.
        :param password: The user's hashed password.
        :param username: The user's username (auto-generated if not provided).
        :param user_type_id: The user's type ID.
        :param description: The user's description.
        :param meta_data: The user's metadata.
        :param is_active: Whether the user is active.
        :return: An instance of Users.
        """
        if not username:
            username = f"{first_name.lower()}.{last_name.lower()}"
        
        return cls(
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            phone=phone,
            password=password,
            username=username,
            user_type_id=user_type_id,
            description=description,
            meta_data=meta_data,
            is_active=is_active,
        )


class UserRoleLink(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """Model for representing user role link information.

    Attributes:
        client_id (str): The client id.
        user_id (str): The user id.
        role_id (str): The role id.
    """

    __tablename__ = "user_role_link"

    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id", use_alter=True, ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", use_alter=True, ondelete="CASCADE"), nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", use_alter=True, ondelete="CASCADE"), nullable=False)

    user: Mapped["Users"] = relationship(
        back_populates="role_links", primaryjoin="UserRoleLink.user_id == Users.id"
    )
    role: Mapped["Roles"] = relationship(
        "Roles", back_populates="user_role_links", foreign_keys=[role_id]
    )
    client: Mapped["Clients"] = relationship(
        "Clients", back_populates="user_role_links", foreign_keys=[client_id]
    )
