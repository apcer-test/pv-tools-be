from apps.case.constants import messages
from core.exceptions import BadRequestError, NotFoundError


class DuplicateConfigNameError(BadRequestError):
    """Exception raised when trying to create a configuration with a duplicate name."""

    message = messages.DUPLICATE_CONFIG_NAME


class DuplicateConfigComponentsError(BadRequestError):
    """Exception raised when trying to create a configuration with duplicate components."""

    message = messages.DUPLICATE_CONFIG_COMPONENTS


class ConfigurationNotFoundError(NotFoundError):
    """Exception raised when a configuration is not found."""

    message = messages.CONFIG_NOT_FOUND


class NoActiveConfigurationError(BadRequestError):
    """Exception raised when no active configuration exists."""

    message = messages.NO_ACTIVE_CONFIG


class DuplicateOrderingError(BadRequestError):
    """Exception raised when configuration components have duplicate ordering."""

    message = messages.DUPLICATE_ORDERING


class InvalidOrderingSequenceError(BadRequestError):
    """Exception raised when configuration component ordering is not sequential."""

    message = messages.INVALID_ORDERING_SEQUENCE


class MultipleSequenceTypesError(BadRequestError):
    """Exception raised when multiple sequence types are used in configuration."""

    message = messages.MULTIPLE_SEQUENCE_TYPES


class CaseNotFoundError(NotFoundError):
    """Exception raised when a case is not found."""

    message = messages.CASE_NOT_FOUND


class DuplicateCaseNumberError(BadRequestError):
    """Exception raised when trying to create a case with a duplicate case number."""

    message = messages.DUPLICATE_CASE_NUMBER
