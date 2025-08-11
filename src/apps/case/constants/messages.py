"""Constants for error messages in the case module."""

# Configuration related messages
DUPLICATE_CONFIG_NAME = "A configuration with this name already exists"
DUPLICATE_CONFIG_COMPONENTS = "A configuration with the same components already exists"
CONFIG_NOT_FOUND = "Configuration not found"
NO_ACTIVE_CONFIG = "No active case number configuration found"

# Component validation messages
DUPLICATE_ORDERING = "Duplicate ordering number found in configuration components"
INVALID_ORDERING_SEQUENCE = (
    "Component ordering must form a continuous sequence starting from 1"
)
MULTIPLE_SEQUENCE_TYPES = "Configuration can only use one type of sequence: SEQUENCE_MONTH, SEQUENCE_YEAR, or SEQUENCE_RUNNING"

# Case related messages
CASE_NOT_FOUND = "Case not found"
DUPLICATE_CASE_NUMBER = "Case number already exists"
MAX_PROMPT_LENGTH = 50
MAX_SEPARATOR_LENGTH = 10