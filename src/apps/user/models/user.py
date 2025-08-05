import uuid
from typing import TYPE_CHECKING, Self

from sqlalchemy.orm import Mapped, mapped_column, relationship
from ulid import ULID

from core.db import Base
from core.types import RoleType
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin

if TYPE_CHECKING:
    from apps.tenant.models.models import Tenant, TenantUsers


class UserModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """
    Model for representing user information.

    This SQLAlchemy model represents user information, including fields such as first_name, last_name, email, phone,
    password, and role. It is used to store and manage user data in the application's database.

    Attributes:
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        email (str): The user's email address (unique).
        phone (str): The user's phone number (unique).
        password (str): The user's hashed password.
        role (int): The user's role identifier.
    """

    __tablename__ = "users"
    first_name: Mapped[str] = mapped_column(index=True)
    last_name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    phone: Mapped[str] = mapped_column(index=True, unique=True)
    password: Mapped[str] = mapped_column()
    role: Mapped[RoleType] = mapped_column()
    tenants: Mapped[list["Tenant"]] = relationship(
        "Tenant",
        secondary="tenant_users",
        back_populates="users",
        primaryjoin="UserModel.id == TenantUsers.user_id",
        secondaryjoin="TenantUsers.tenant_id == Tenant.id",
        viewonly=True,
    )

    tenant_users: Mapped[list["TenantUsers"]] = relationship(
        "TenantUsers",
        back_populates="user",
        primaryjoin="UserModel.id == TenantUsers.user_id",
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
        role: str = RoleType.USER,
    ) -> Self:
        """
        Create a new user.

        :param first_name: The user's first name.
        :param last_name: The user's last name.
        :param phone: The user's phone number.
        :param email: The user's email address.
        :param password: The user's hashed password.
        :param role: The user's role identifier. Defaults to RoleType.USER.
        :return: An instance of UserModel.
        """
        return cls(
            id=str(ULID()),
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            phone=phone,
            password=password,
            role=role,
        )
