from enum import StrEnum


class ModuleMessage(StrEnum):
    MODULE_ALREADY_EXISTS = "Module already exists!"
    MODULE_NOT_EXISTS = "Module does not exists!"
    MODULE_ASSIGNED_FOUND = "Module assigned to user.You are Not allow to delete"
    MODULE_DELETED = "Module deleted successfully"


class ModuleSortBy(StrEnum):
    """Define enum type for sort by options"""

    NAME = "NAME"
    CREATED_AT = "CREATED_AT"
