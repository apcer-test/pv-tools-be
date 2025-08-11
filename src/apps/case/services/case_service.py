from datetime import datetime
from typing import Annotated, List, Optional, Union

from fastapi import Depends
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.case.exceptions import (
    ConfigurationNotFoundError,
    DuplicateCaseNumberError,
    DuplicateConfigComponentsError,
    NoActiveConfigurationError,
)
from apps.case.models.case import (
    Case,
    CaseNumberComponent,
    CaseNumberConfiguration,
    CaseSequenceTracker,
)
from apps.case.schemas.request import (
    CaseCreate,
    CaseNumberComponentCreate,
    CaseNumberConfigurationCreate,
)
from apps.case.types.component_types import ComponentType
from core.db import db_session


def _get_component_signature(
    component: Union[CaseNumberComponent, CaseNumberComponentCreate]
) -> str:
    """Get a unique signature for a component based on its properties"""
    return f"{component.component_type}:{component.size or 'None'}:{component.prompt or 'None'}"


def _components_match(
    components1: List[Union[CaseNumberComponent, CaseNumberComponentCreate]],
    components2: List[Union[CaseNumberComponent, CaseNumberComponentCreate]],
) -> bool:
    """Check if two lists of components are equivalent (ignoring order)"""
    if len(components1) != len(components2):
        return False

    # Convert components to sets of signatures for comparison
    sigs1 = {_get_component_signature(c) for c in components1}
    sigs2 = {_get_component_signature(c) for c in components2}

    return sigs1 == sigs2


def _get_component_name(
    component: Union[CaseNumberComponent, CaseNumberComponentCreate]
) -> str:
    """Get a display name for a component"""
    if component.component_type == ComponentType.PROMPT:
        return component.prompt or "PROMPT"
    return ComponentType.get_display_name(component.component_type)


def _generate_config_name(
    components: List[Union[CaseNumberComponent, CaseNumberComponentCreate]],
    separator: str,
) -> str:
    """Generate a configuration name based on components"""
    # Sort components by ordering
    sorted_components = sorted(components, key=lambda x: x.ordering)
    # Get component names
    component_names = [_get_component_name(c) for c in sorted_components]
    # Join with separator
    return separator.join(component_names) if separator else component_names[0]


class CaseService:
    """Service for managing cases and case number generation"""

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]):
        """Initialize the CaseService with a database session"""
        self.session = session

    async def _check_components_exist(
        self, components: List[CaseNumberComponentCreate]
    ) -> bool:
        """Check if a configuration with the same components already exists"""
        # Get all configurations with their components
        configs = await self.session.scalars(
            select(CaseNumberConfiguration).options(
                selectinload(CaseNumberConfiguration.components)
            )
        )

        # Check each configuration's components
        for config in configs:
            if _components_match(components, config.components):
                return True

        return False

    async def _deactivate_current_active_config(self) -> None:
        """Deactivate the currently active configuration"""
        await self.session.execute(
            update(CaseNumberConfiguration)
            .where(CaseNumberConfiguration.is_active == True)  # noqa: E712
            .values(is_active=False)
        )

    async def set_configuration_active(self, config_id: str) -> CaseNumberConfiguration:
        """Set a configuration as active and deactivate others"""
        # Check if configuration exists
        config = await self.get_configuration(config_id)
        if not config:
            raise ConfigurationNotFoundError

        # Deactivate all configurations
        await self._deactivate_current_active_config()

        # Set the specified configuration as active
        config.is_active = True
        await self.session.flush()

        return config

    async def create_configuration(
        self, config: CaseNumberConfigurationCreate
    ) -> CaseNumberConfiguration:
        """Create a new case number configuration"""
        # Check for duplicate components
        if await self._check_components_exist(config.components):
            raise DuplicateConfigComponentsError

        # Generate configuration name
        config_name = _generate_config_name(config.components, config.separator or "")

        # Deactivate current active configuration
        await self._deactivate_current_active_config()

        # Create configuration (set as active)
        config_obj = CaseNumberConfiguration(
            name=config_name,
            separator=config.separator or "",  # Use empty string for single component
            is_active=True,  # New configuration is always active
        )
        self.session.add(config_obj)
        await self.session.flush()  # Generate ID for foreign key references

        # Create components
        for component in config.components:
            component_obj = CaseNumberComponent(
                config_id=config_obj.id,
                component_type=component.component_type,
                size=component.size,
                prompt=component.prompt,
                ordering=component.ordering,
            )
            self.session.add(component_obj)

        return config_obj

    async def get_active_configuration(self) -> Optional[CaseNumberConfiguration]:
        """Get the currently active configuration"""
        return await self.session.scalar(
            select(CaseNumberConfiguration)
            .options(selectinload(CaseNumberConfiguration.components))
            .where(CaseNumberConfiguration.is_active == True)  # noqa: E712
        )

    async def get_configuration(
        self, config_id: str
    ) -> Optional[CaseNumberConfiguration]:
        """Get a case number configuration by ID"""
        return await self.session.scalar(
            select(CaseNumberConfiguration)
            .options(selectinload(CaseNumberConfiguration.components))
            .where(CaseNumberConfiguration.id == config_id)
        )

    async def list_configurations(
        self, is_active: Optional[bool] = None
    ) -> List[CaseNumberConfiguration]:
        """List configurations with optional active status filter.

        Args:
            is_active: If provided, filter configurations by active status

        Returns:
            List of configurations matching the filter
        """
        query = select(CaseNumberConfiguration).options(
            selectinload(CaseNumberConfiguration.components)
        )

        if is_active is not None:
            query = query.where(CaseNumberConfiguration.is_active == is_active)

        query = query.order_by(CaseNumberConfiguration.created_at.desc())
        return (await self.session.scalars(query)).all()

    async def _get_sequence_component(
        self, components: List[CaseNumberComponent]
    ) -> tuple[Optional[CaseNumberComponent], Optional[ComponentType]]:
        """Get the sequence component and its type from the configuration"""
        sequence_types = {
            ComponentType.SEQUENCE_MONTH,
            ComponentType.SEQUENCE_YEAR,
            ComponentType.SEQUENCE_RUNNING,
        }

        for component in components:
            if component.component_type in sequence_types:
                return component, component.component_type

        return None, None

    async def _get_or_create_sequence_tracker(
        self, config_id: str, sequence_type: ComponentType
    ) -> CaseSequenceTracker:
        """Get or create a sequence tracker based on sequence type.

        Each configuration maintains its own sequence counter:
        - SEQUENCE_MONTH: Tracks by year_month (YYYYMM)
        - SEQUENCE_YEAR: Tracks by year (YYYY)
        - SEQUENCE_RUNNING: Tracks only by config_id
        """
        current_date = datetime.now()

        # Query existing tracker
        query = select(CaseSequenceTracker).where(
            CaseSequenceTracker.config_id == config_id
        )

        match sequence_type:
            case ComponentType.SEQUENCE_MONTH:
                # For monthly sequence, track by year and month
                year_month = current_date.strftime("%Y%m")
                year = current_date.strftime("%Y")
                query = query.where(CaseSequenceTracker.year_month == year_month)
                tracker = await self.session.scalar(query)
                if not tracker:
                    tracker = CaseSequenceTracker(
                        config_id=config_id,
                        year=year,
                        year_month=year_month,
                        current_value=0,
                    )
                    self.session.add(tracker)
                    await self.session.flush()

            case ComponentType.SEQUENCE_YEAR:
                # For yearly sequence, track by year only
                year = current_date.strftime("%Y")
                query = query.where(CaseSequenceTracker.year == year)
                tracker = await self.session.scalar(query)
                if not tracker:
                    tracker = CaseSequenceTracker(
                        config_id=config_id,
                        year=year,
                        year_month=None,  # Not needed for yearly
                        current_value=0,
                    )
                    self.session.add(tracker)
                    await self.session.flush()

            case ComponentType.SEQUENCE_RUNNING:
                # For running sequence, track only by config_id
                # Get the latest tracker for this config
                query = query.where(
                    CaseSequenceTracker.year.is_(None),
                    CaseSequenceTracker.year_month.is_(None),
                ).order_by(CaseSequenceTracker.current_value.desc())
                tracker = await self.session.scalar(query)
                if not tracker:
                    tracker = CaseSequenceTracker(
                        config_id=config_id,
                        year=None,  # Not needed for running sequence
                        year_month=None,  # Not needed for running sequence
                        current_value=0,
                    )
                    self.session.add(tracker)
                    await self.session.flush()

        if not tracker:
            self.session.add(tracker)
            await self.session.flush()
        else:
            tracker.current_value += 1

        return tracker

    async def _generate_case_number(self, config: CaseNumberConfiguration) -> str:
        """Generate a case number based on the configuration"""
        # Components are already loaded due to selectinload in get_configuration
        components = sorted(config.components, key=lambda x: x.ordering)
        parts = []
        current_date = datetime.now()
        year_month = current_date.strftime("%Y%m")

        # Get sequence component and type
        sequence_component, sequence_type = await self._get_sequence_component(
            components
        )

        for component in components:
            value = ""

            match component.component_type:
                case ComponentType.PROMPT:
                    value = component.prompt or ""
                case ComponentType.YYYYMM:
                    value = year_month
                case ComponentType.YYYY:
                    value = current_date.strftime("%Y")
                case ComponentType.YY:
                    value = current_date.strftime("%y")
                case ComponentType.YYMM:
                    value = current_date.strftime("%y%m")
                case (
                    ComponentType.SEQUENCE_MONTH
                    | ComponentType.SEQUENCE_YEAR
                    | ComponentType.SEQUENCE_RUNNING
                ):
                    if sequence_type:
                        tracker = await self._get_or_create_sequence_tracker(
                            config.id, sequence_type
                        )
                        value = str(tracker.current_value).zfill(component.size or 5)
                case ComponentType.INITIAL_UNIT:
                    # TODO: Implement based on Company Unit, we have one company unit which is set as primary company unit
                    value = "UNIT"
                case ComponentType.OWNER_UNIT:
                    # TODO: Implement later
                    value = "OWNER"

            if component.size:
                value = value[: component.size]

            parts.append(value)

        return config.separator.join(parts)

    async def create_case(self, case_data: CaseCreate) -> Case:
        """Create a new case with generated case number"""

        # Get active configuration
        config = await self.get_active_configuration()
        if not config:
            raise NoActiveConfigurationError

        # Generate case number
        case_number = await self._generate_case_number(config)

        # Check if case number already exists
        existing_case = await self.get_case_by_number(case_number)
        if existing_case:
            raise DuplicateCaseNumberError

        # Create case
        case = Case(
            case_number=case_number, config_id=config.id, meta_data=case_data.meta_data
        )
        self.session.add(case)
        await self.session.flush()

        return case

    async def get_case(self, case_number: str) -> Optional[Case]:
        """Get a case by ID"""
        response = await self.session.execute(
            select(Case)
            .options(selectinload(Case.config))
            .where(Case.case_number == case_number)
        )
        return response.scalar_one_or_none()

    async def get_case_by_number(self, case_number: str) -> Optional[Case]:
        """Get a case by case number"""
        response = await self.session.execute(
            select(Case)
            .options(selectinload(Case.config))
            .where(Case.case_number == case_number)
        )
        return response.scalar_one_or_none()

    async def update_configuration(
        self, config_id: str, config: CaseNumberConfigurationCreate
    ) -> CaseNumberConfiguration:
        """Update an existing case number configuration.

        Args:
            config_id: ID of the configuration to update
            config: New configuration data

        Returns:
            Updated configuration

        Raises:
            ConfigurationNotFoundError: If configuration not found
            DuplicateConfigComponentsError: If resulting config would be duplicate
            CannotModifyActiveConfigError: If trying to modify active config
        """
        # Get existing configuration with components
        existing_config = await self.get_configuration(config_id)
        if not existing_config:
            raise ConfigurationNotFoundError

        # Active configurations can be modified

        # Check for duplicate components (excluding current config)
        configs = await self.session.scalars(
            select(CaseNumberConfiguration)
            .options(selectinload(CaseNumberConfiguration.components))
            .where(CaseNumberConfiguration.id != config_id)
        )

        for other_config in configs:
            if _components_match(config.components, other_config.components):
                raise DuplicateConfigComponentsError

        # Generate new name based on components
        new_name = _generate_config_name(config.components, config.separator or "")

        async with self.session.begin_nested():
            # Update main configuration
            existing_config.name = new_name
            existing_config.separator = config.separator or ""

            # Track existing component IDs
            existing_ids = {c.id for c in existing_config.components}
            updated_ids = set()

            # Update/create components
            for new_component in config.components:
                if hasattr(new_component, "id") and new_component.id:
                    # Update existing component
                    component = await self.session.scalar(
                        select(CaseNumberComponent).where(
                            CaseNumberComponent.id == new_component.id,
                            CaseNumberComponent.config_id == config_id,
                        )
                    )
                    if component:
                        component.component_type = new_component.component_type
                        component.size = new_component.size
                        component.prompt = new_component.prompt
                        component.ordering = new_component.ordering
                        updated_ids.add(component.id)
                else:
                    # Create new component
                    component = CaseNumberComponent(
                        config_id=config_id,
                        component_type=new_component.component_type,
                        size=new_component.size,
                        prompt=new_component.prompt,
                        ordering=new_component.ordering,
                    )
                    self.session.add(component)

            # Delete removed components
            for component_id in existing_ids - updated_ids:
                await self.session.execute(
                    delete(CaseNumberComponent).where(
                        CaseNumberComponent.id == component_id
                    )
                )

            # Handle sequence trackers if sequence type changed
            old_sequence = await self._get_sequence_component(
                existing_config.components
            )
            new_sequence = await self._get_sequence_component(
                [c for c in config.components if isinstance(c, CaseNumberComponent)]
            )

            if old_sequence[1] != new_sequence[1]:
                # Delete old sequence trackers
                await self.session.execute(
                    delete(CaseSequenceTracker).where(
                        CaseSequenceTracker.config_id == config_id
                    )
                )

            await self.session.flush()

        # Refresh configuration with updated components
        await self.session.refresh(existing_config)
        return existing_config
