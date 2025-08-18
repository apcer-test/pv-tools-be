from apps.clients.constants import ClientMessage
from core.exceptions import (
    AlreadyExistsError,
    BadRequestError,
    NotFoundError,
    UnprocessableEntityError,
)


class ClientAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a client that already exists."""

    message = ClientMessage.CLIENT_ALREADY_EXISTS


class ClientNotFoundError(NotFoundError):
    """Exception raised when a client is not found."""

    message = ClientMessage.CLIENT_NOT_EXISTS


class EmptyDescriptionError(UnprocessableEntityError):
    """Custom exception for issue with the notes create empty description."""

    message = ClientMessage.DESCRIPTION


class InvalidEncryptedDataError(BadRequestError):
    """Custom exception for User already assigned error."""

    message = ClientMessage.INVALID_ENCRYPTED_DATA
