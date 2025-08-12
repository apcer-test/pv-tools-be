from apps.permissions.constants import PermissionMessage
from core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError


class PermissionAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a permission that already exists."""

    message = PermissionMessage.PERMISSION_ALREADY_EXISTS


class PermissionNotFoundError(NotFoundError):
    """Custom exception to show a generic error message."""

    message = PermissionMessage.PERMISSION_NOT_EXISTS


class PermissionAssignedFoundError(BadRequestError):
    """Exception raised when attempting to delete a permission that
    already assigned to user."""

    message = PermissionMessage.PERMISSION_ASSIGNED_FOUND


class InvalidModulePermissionError(BadRequestError):
    """Exception raised when attempting to invalid module permission."""

    message = PermissionMessage.INVALID_MODULE_PERMISSION
