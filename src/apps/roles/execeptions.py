from apps.roles.constants import RoleMessage
from core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError


class RoleAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a role that already exists."""

    message = RoleMessage.ROLE_ALREADY_EXISTS


class RoleNotFoundError(NotFoundError):
    """Custom exception to show a generic error message."""

    message = RoleMessage.ROLE_NOT_EXISTS


class RoleAssignedFoundError(BadRequestError):
    """Exception raised when attempting to delete a permission that
    already assigned to user."""

    message = RoleMessage.ROLE_ASSIGNED_FOUND
