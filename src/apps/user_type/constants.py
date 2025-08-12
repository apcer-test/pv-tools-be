"""for constant messages."""

from enum import StrEnum


class UserTypeSortBy(StrEnum):
    """Define enum type for sort by options."""

    NAME = "NAME"
    CREATED_AT = "CREATED_AT"


class UserTypeMessage(StrEnum):
    """Error messages."""

    USERTYPE_ALREADY_EXISTS = "Usertype already exists!"
    USERTYPE_NOT_EXISTS = "Usertype does not exists!"
    USERTYPE_ASSIGNED_FOUND = "UserType assigned to user.You are Not allow to delete"
    USERTYPE_DELETED = "User Type deleted successfully."
    INVALID_USERTYPE = "Invalid User type."
