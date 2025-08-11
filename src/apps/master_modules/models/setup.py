from typing import TYPE_CHECKING, List

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin, UserMixin


class LookupModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """
    Model representing master lookup models like Country, State, etc.
    """
    __tablename__ = "lookup_model"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    lookup_type: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True, server_default="True")

    # Relationships
    lookup_values: Mapped[List["LookupValuesModel"]] = relationship(
        "LookupValuesModel",
        back_populates="lookup_model",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LookupModel(id={self.id}, name={self.name})>"


class LookupValuesModel(Base, ULIDPrimaryKeyMixin, TimeStampMixin, UserMixin):
    """
    Model representing lookup values of lookup models like specific countries.
    """
    __tablename__ = "lookup_values_model"

    lookup_model_id: Mapped[str] = mapped_column(
        ForeignKey("lookup_model.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    e2b_code_r2: Mapped[str | None] = mapped_column(String(100))
    e2b_code_r3: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True, server_default="True")

    # Relationships
    lookup_model: Mapped["LookupModel"] = relationship(
        "LookupModel",
        back_populates="lookup_values"
    )

    # Unique constraint for name within a module
    __table_args__ = (
        UniqueConstraint("lookup_model_id", "name", name="uq_lookup_model_name"),
    )

    def __repr__(self) -> str:
        return f"<LookupValuesModel(id={self.id}, lookup_model_id={self.lookup_model_id}, name={self.name})>"
