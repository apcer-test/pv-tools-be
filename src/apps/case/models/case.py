from typing import List, Optional

from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.case.types.component_types import ComponentType
from core.db import Base
from core.utils.mixins import TimeStampMixin, ULIDPrimaryKeyMixin


class CaseNumberConfiguration(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """Configuration for case number generation patterns"""

    __tablename__ = "case_number_configurations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    separator: Mapped[str] = mapped_column(String(10), default="-")
    is_active: Mapped[bool] = mapped_column(default=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON)

    # Relationships
    components: Mapped[List["CaseNumberComponent"]] = relationship(
        "CaseNumberComponent", back_populates="config", cascade="all, delete-orphan"
    )
    sequence_trackers: Mapped[List["CaseSequenceTracker"]] = relationship(
        "CaseSequenceTracker", back_populates="config", cascade="all, delete-orphan"
    )
    cases: Mapped[List["Case"]] = relationship(
        "Case", back_populates="config", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of the case number configuration"""
        return f"<CaseNumberConfiguration(id={self.id}, name={self.name})>"


class CaseNumberComponent(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """Individual components that make up a case number pattern"""

    __tablename__ = "case_number_components"

    config_id: Mapped[str] = mapped_column(
        ForeignKey("case_number_configurations.id"), nullable=False
    )
    component_type: Mapped[ComponentType] = mapped_column(Integer, nullable=False)
    size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ordering: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    config: Mapped["CaseNumberConfiguration"] = relationship(
        "CaseNumberConfiguration", back_populates="components"
    )

    def __repr__(self) -> str:
        """String representation of the case number component"""
        return f"<CaseNumberComponent(id={self.id}, type={ComponentType.get_display_name(self.component_type)}, ordering={self.ordering})>"


class CaseSequenceTracker(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """Tracks sequence numbers for case number generation"""

    __tablename__ = "case_sequence_trackers"

    config_id: Mapped[str] = mapped_column(
        ForeignKey("case_number_configurations.id"), nullable=False
    )
    year_month: Mapped[str] = mapped_column(String(6), nullable=False)  # Format: YYYYMM
    year: Mapped[str] = mapped_column(String(4), nullable=False)  # Format: YYYY
    current_value: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    config: Mapped["CaseNumberConfiguration"] = relationship(
        "CaseNumberConfiguration", back_populates="sequence_trackers"
    )

    __table_args__ = (
        UniqueConstraint("config_id", "year_month", name="uq_tracker_config_month"),
        UniqueConstraint("config_id", "year", name="uq_tracker_config_year"),
    )

    def __repr__(self) -> str:
        """String representation of the case sequence tracker"""
        return f"<CaseSequenceTracker(id={self.id}, year_month={self.year_month}, current={self.current_value})>"


class Case(Base, ULIDPrimaryKeyMixin, TimeStampMixin):
    """Main case table"""

    __tablename__ = "cases"

    case_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    config_id: Mapped[str] = mapped_column(ForeignKey("case_number_configurations.id"))
    version: Mapped[str] = mapped_column(String(50), default="0.0")
    meta_data: Mapped[dict | None] = mapped_column(JSON)

    # Relationships
    config: Mapped["CaseNumberConfiguration"] = relationship(
        "CaseNumberConfiguration", back_populates="cases"
    )

    def __repr__(self) -> str:
        """String representation of the case"""
        return f"<Case(id={self.id}, case_number={self.case_number})>"
