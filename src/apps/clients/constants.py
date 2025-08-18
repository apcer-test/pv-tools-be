from enum import StrEnum


class ClientSortBy(StrEnum):
    """Define enum type for sort by options"""

    NAME = "NAME"


class ClientMessage(StrEnum):
    CLIENT_ALREADY_EXISTS = "Client already exists!"
    CLIENT_NOT_EXISTS = "Client does not exists!"
    DESCRIPTION = "Please provide a description."
    INVALID_ENCRYPTED_DATA = "Invalid encrypted data."
    CLIENT_CREATED = "Client created successfully"
    CLIENT_UPDATED = "Client updated successfully"
