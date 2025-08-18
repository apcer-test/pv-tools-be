from enum import StrEnum


class PermissionMessage(StrEnum):
    PERMISSION_ALREADY_EXISTS = "Permission already exists!"
    PERMISSION_NOT_EXISTS = "Permission does not exists!"
    PERMISSION_ASSIGNED_FOUND = (
        "Permission assigned to user.You are Not allow to delete"
    )
    INVALID_MODULE_PERMISSION = "Invalid Permission For Module"


class PermissionSortBy(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
