from apps.modules.constants import ModuleMessage
from core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError


class ModuleAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a permission that already exists."""

    message = ModuleMessage.MODULE_ALREADY_EXISTS


class ModuleNotFoundCustomError(NotFoundError):
    """Custom exception to show a generic error message."""

    message = ModuleMessage.MODULE_NOT_EXISTS


class ModuleAssignedFoundError(BadRequestError):
    """Exception raised when attempting to delete a permission that
    already assigned to user."""

    message = ModuleMessage.MODULE_ASSIGNED_FOUND
