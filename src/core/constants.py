from enum import StrEnum

ACCESS = "access"
REFRESH = "refresh"


class ErrorMessage(StrEnum):
    INVALID_JWT_TOKEN = "Invalid Token"  # noqa: S105
    EXPIRED_TOKEN = "Expired Token"  # noqa: S105
    UNAUTHORIZED = "Unauthorized"
    SOMETHING_WENT_WRONG = "Something went wrong"
    FORBIDDEN = "Forbidden"
    NAIVE_DATETIME_NOT_ALLOWED = "Naive datetime is disallowed"


class SortType(StrEnum):
    ASC = "ASC"
    DSC = "DSC"

CONTENT_TYPE = "application/x-www-form-urlencoded"
GRANT_TYPE = "authorization_code"
ACCESS_TOKEN_SCOPE = "openid profile offline_access email Mail.Read"
ACCESS_TOKEN_GRANT_TYPE = "refresh_token"