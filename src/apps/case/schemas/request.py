from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from apps.case.exceptions import (
    DuplicateOrderingError,
    InvalidOrderingSequenceError,
    MultipleSequenceTypesError,
)
from apps.case.types.component_types import ComponentType
from core.utils import CamelCaseModel


class CaseNumberComponentCreate(CamelCaseModel):
    """Schema for creating a case number component"""

    component_type: ComponentType = Field(..., description="Type of the component")
    size: Optional[int] = Field(
        None, description="Size of the component (if applicable)"
    )
    prompt: Optional[str] = Field(
        None, description="Prompt text for PROMPT type components"
    )
    ordering: int = Field(..., description="Order of the component in the case number")

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, prompt: Optional[str], info) -> Optional[str]:
        """Validate that prompt is provided for PROMPT type components"""
        component_type = info.data.get("component_type")
        if component_type == ComponentType.PROMPT and not prompt:
            raise ValueError("Prompt is required for PROMPT type components")
        return prompt


class CaseNumberConfigurationCreate(CamelCaseModel):
    """Schema for creating a case number configuration"""

    components: List[CaseNumberComponentCreate] = Field(
        ..., description="List of components that make up the case number"
    )
    separator: Optional[str] = Field(
        None,
        description="Separator between components. Required when there are multiple components.",
    )

    @field_validator("separator")
    @classmethod
    def validate_separator(cls, separator: Optional[str], info) -> Optional[str]:
        """Validate separator based on number of components"""
        components = info.data.get("components", [])
        if len(components) > 1 and not separator:
            raise ValueError("Separator is required when there are multiple components")
        return separator or ""

    @field_validator("components")
    @classmethod
    def validate_sequence_types(
        cls, components: List[CaseNumberComponentCreate]
    ) -> List[CaseNumberComponentCreate]:
        """Validate that only one type of sequence component is used"""
        sequence_types = {
            ComponentType.SEQUENCE_MONTH,
            ComponentType.SEQUENCE_YEAR,
            ComponentType.SEQUENCE_RUNNING,
        }
        found_sequences = {
            c.component_type for c in components if c.component_type in sequence_types
        }
        if len(found_sequences) > 1:
            raise MultipleSequenceTypesError
        return components

    @field_validator("components")
    @classmethod
    def validate_unique_ordering(
        cls, components: List[CaseNumberComponentCreate]
    ) -> List[CaseNumberComponentCreate]:
        """Validate that ordering numbers are unique"""
        order_numbers = {}
        for component in components:
            if component.ordering in order_numbers:
                raise DuplicateOrderingError
            order_numbers[component.ordering] = component
        return components

    @field_validator("components")
    @classmethod
    def validate_ordering_sequence(
        cls, components: List[CaseNumberComponentCreate]
    ) -> List[CaseNumberComponentCreate]:
        """Validate that ordering numbers form a continuous sequence starting from 1"""
        if not components:
            raise InvalidOrderingSequenceError

        orders = sorted(c.ordering for c in components)
        expected = list(range(1, len(components) + 1))

        if orders != expected:
            raise InvalidOrderingSequenceError

        return components


class CaseCreate(CamelCaseModel):
    """Schema for creating a new case"""

    meta_data: Optional[dict] = Field(
        None, description="Additional metadata for the case"
    )
