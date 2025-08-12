from enum import StrEnum


class ClientSortBy(StrEnum):
    """Define enum type for sort by options"""

    NAME = "NAME"


class ClientMessage(StrEnum):
    CLIENT_DELETED = "Client deleted successfully"
    CLIENT_ALREADY_EXISTS = "Client already exists!"
    CLIENT_NOT_EXISTS = "Client does not exists!"
    DESCRIPTION = "Please provide a description."
    INVALID_ENCRYPTED_DATA = "Invalid encrypted data."
