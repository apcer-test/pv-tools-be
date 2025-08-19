from enum import IntEnum, StrEnum

ACCESS = "access"
REFRESH = "refresh"


class ErrorMessage(StrEnum):
    """This class represents the error messages for the application."""

    INVALID_JWT_TOKEN = "Invalid Token"  # noqa: S105
    EXPIRED_TOKEN = "Expired Token"  # noqa: S105
    UNAUTHORIZED = "Unauthorized"
    SOMETHING_WENT_WRONG = "Something went wrong"
    FORBIDDEN = "Forbidden"
    NAIVE_DATETIME_NOT_ALLOWED = "Naive datetime is disallowed"


class SortType(StrEnum):
    """This class represents the sort type for the application."""

    ASC = "ASC"
    DSC = "DSC"


class RedisTTL(IntEnum):
    """
    Redis TTL for the API
    """

    AICB_MEDDRA_VERSION_LIST = 3600  # 3600s = 1h
