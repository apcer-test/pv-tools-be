from typing import List, Optional

from pydantic import Field, field_validator

from apps.case.exceptions import (
    DuplicateOrderingError,
    InvalidOrderingSequenceError,
    MultipleSequenceTypesError,
)
from apps.case.constants import messages
from apps.case.types.component_types import ComponentType
from core.utils import CamelCaseModel


class CaseNumberComponentCreate(CamelCaseModel):
    """Schema for creating a case number component."""

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
        """Validate that prompt is provided for PROMPT type components.

        Args:
            prompt: The prompt text
            info: Validation context containing other field values

        Returns:
            The validated prompt text

        Raises:
            ValueError: If prompt is required but not provided
        """
        component_type = info.data.get("component_type")
        if component_type == ComponentType.PROMPT and not prompt.strip():
            raise ValueError("Prompt is required for PROMPT type components")
        if component_type == ComponentType.PROMPT and len(prompt) > messages.MAX_PROMPT_LENGTH:
            raise ValueError(f"Prompt must be less than {messages.MAX_PROMPT_LENGTH} characters")
        return prompt


class CaseNumberConfigurationCreate(CamelCaseModel):
    """Schema for creating a case number configuration."""

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
        """Validate separator based on number of components and max length."""
        components = info.data.get("components", [])
        if len(components) > 1 and not separator.strip():
            raise ValueError("Separator is required when there are multiple components")
        if separator and len(separator) > messages.MAX_SEPARATOR_LENGTH:
            raise ValueError(f"Separator must be at most {messages.MAX_SEPARATOR_LENGTH} characters")
        return separator or ""

    @field_validator("components")
    @classmethod
    def validate_sequence_types(
        cls, components: List[CaseNumberComponentCreate]
    ) -> List[CaseNumberComponentCreate]:
        """Validate that only one type of sequence component is used.

        Args:
            components: List of components to validate

        Returns:
            The validated components list

        Raises:
            MultipleSequenceTypesError: If multiple sequence types are found
        """
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
        """Validate that ordering numbers are unique.

        Args:
            components: List of components to validate

        Returns:
            The validated components list

        Raises:
            DuplicateOrderingError: If duplicate ordering numbers are found
        """
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
        """Validate that ordering numbers form a continuous sequence starting from 1.

        Args:
            components: List of components to validate

        Returns:
            The validated components list

        Raises:
            InvalidOrderingSequenceError: If sequence is not continuous or doesn't start from 1
        """
        if not components:
            raise InvalidOrderingSequenceError

        orders = sorted(c.ordering for c in components)
        expected = list(range(1, len(components) + 1))

        if orders != expected:
            raise InvalidOrderingSequenceError

        return components


class CaseCreate(CamelCaseModel):
    """Schema for creating a new case."""

    meta_data: Optional[dict] = Field(
        None, description="Additional metadata for the case"
    )
