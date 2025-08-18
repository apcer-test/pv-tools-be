from enum import StrEnum


class RolesSortBy(StrEnum):
    """Define enum type for sort by options"""

    NAME_DESC = "name_desc"
    NAME_ASC = "name_asc"


class RoleMessage(StrEnum):
    ROLE_ALREADY_EXISTS = "Role already exists!"
    ROLE_NOT_EXISTS = "Role does not exists!"
    ROLE_ASSIGNED_FOUND = "Role assigned to user.You are Not allow to delete"
