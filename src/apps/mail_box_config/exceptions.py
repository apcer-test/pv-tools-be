from src import constants
from src.core.exceptions import BadRequestError, CustomException, NotFoundError


class MailBoxAlreadyConfigured(BadRequestError):
    """Custom exception to show a generic error message."""

    message = constants.MAILBOX_ALREADY_CONFIGURED

class InvalidTokenException(CustomException):
    """Exception raised when the token is invalid."""

    message = constants.INVALID_AUTH_TOKEN

class MailBoxConfigNotFound(NotFoundError):
    """Custom exception to show a generic error message."""

    message = constants.MAILBOX_CONFIG_NOT_FOUND

class StartDateException(BadRequestError):
    """Custom exception to show a generic error message."""

    message = constants.START_DATE_INVALID

class EndDateException(BadRequestError):
    """Custom exception to show a generic error message."""

    message = constants.END_DATE_INVALID