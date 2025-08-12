"""Request schema for user type."""

from apps.user_types.constants import UserTypeMessage
from core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError


class UserTypeAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a UserType that already exists."""

    message = UserTypeMessage.USERTYPE_ALREADY_EXISTS


class UserTypeNotFoundError(NotFoundError):
    """Custom exception to show a generic error message."""

    message = UserTypeMessage.USERTYPE_NOT_EXISTS


class UserTypeAssignedFoundError(BadRequestError):
    """Exception raised when attempting to delete a Subtype that already
    assigned to user."""

    message = UserTypeMessage.USERTYPE_ASSIGNED_FOUND


class InvalidTypeError(BadRequestError):
    """Exception raised when attempting to delete a Subtype that
    already assigned to user."""

    message = UserTypeMessage.INVALID_USERTYPE
