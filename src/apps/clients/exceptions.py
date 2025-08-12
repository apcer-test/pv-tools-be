from apps.tenants.constants import TenantMessage
from core.exceptions import (
    AlreadyExistsError,
    BadRequestError,
    NotFoundError,
    UnprocessableEntityError,
)


class TenantAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a tenant that already exists."""

    message = TenantMessage.TENANT_ALREADY_EXISTS


class TenantNotFoundError(NotFoundError):
    """Exception raised when a tenant is not found."""

    message = TenantMessage.TENANT_NOT_EXISTS


class EmptyDescriptionError(UnprocessableEntityError):
    """Custom exception for issue with the notes create empty description."""

    message = TenantMessage.DESCRIPTION


class InvalidEncryptedDataError(BadRequestError):
    """Custom exception for User already assigned error."""

    message = TenantMessage.INVALID_ENCRYPTED_DATA
