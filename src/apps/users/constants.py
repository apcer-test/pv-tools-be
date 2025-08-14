from enum import StrEnum


class UserSortBy(StrEnum):
    """Define enum type for sort by options"""

    NAME_DESC = "name_desc"
    NAME_ASC = "name_asc"
    EMAIL_DESC = "email_desc"
    EMAIL_ASC = "email_asc"
    ROLE_ASC = "role_asc"
    ROLE_DESC = "role_desc"
    USER_TYPE_DESC = "user_type_desc"
    USER_TYPE_ASC = "user_type_asc"
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"


class UserErrorMessage(StrEnum):
    PASSWORD_EMPTY = "Password cannot be empty"  # noqa: S105
    USER_NOT_FOUND = "User not found"
    INVALID_CREDS = "Invalid credentials"
    INVALID_ACCESS = "You can't access this page"
    ACCOUNT_LOCKED = (
        "Account is locked due to too many failed attempts. Please try again later."
    )
    TOO_MANY_FAILED_ATTEMPTS = "Too many failed attempts. Please try again later."
    INVALID_OTP = "Invalid OTP"
    INVALID_LOGIN_METHOD_OR_CREDENTIALS = "Invalid login method or credentials"
    INVALID_MFA_CODE = "Invalid MFA code. Please try again."
    MFA_NOT_ENABLED = "MFA is not enabled for your account."
    MFA_NOT_SETUP = "MFA is not set up for your account."
    MFA_ALREADY_ENABLED = "MFA is already enabled for your account."
    MFA_SETUP_REQUIRED = "MFA setup is required for your account."
    MFA_TOKEN_EXPIRED = "MFA code has expired. Please generate a new one."  # noqa: S105
    MFA_TOO_MANY_ATTEMPTS = "Too many failed MFA attempts. Please try again later."
    USER_ALREADY_MFA_ENROLLED = "User already has MFA enrolled."
    INVALID_BACKUP_CODE = "Invalid backup code. Please try again."
    MFA_CODE_REQUIRED = "MFA code is required."
    MFA_NOT_DISABLE = "MFA required at app level can't disabled"


class UserMessage(StrEnum):
    LOGIN_SUCCESS = "Login successful"
    INVALID_PHONE_NUMBER = "Invalid Phone Number"
    WEAK_PASSWORD = "Password is Weak"  # noqa: S105
    ACCOUNT_ALREADY_EXISTS = "Account Already exists"
    USER_DELETED = "User deleted successfully"
    PHONE_NUMER_EXISTS = "Phone number already exists"
    USERNAME_EXISTS = "Username already exists"
    EMAIL_EXISTS = "Email already exists"
    PASSWORD_UPDATE_SUCCESS = "Password updated successfully"  # noqa: S105
    PASSWORD_NOT_MATCH = "Password does not match"  # noqa: S105
    GENERATE_PASSWORD = "Please generate password."  # noqa: S105
    RECENT_PASSWORD_MATCHED = "You cannot reuse a recently used password."  # noqa: S105
    INVALID_PASSWORD = "Invalid current password"  # noqa: S105
    EMAIL_OR_PHONE_REQUIRED = "At least one of email or phone is required."
    PASSWORD_CHANGE_SUCCESS = "Password changed successfully"  # noqa: S105
    PHONE_REQUIRED = "Phone Number is required."
    PHONE_OR_EMAIL_REQUIRED = "At least one of email or phone is required."
    PASSWORD_OR_OTP_REQUIRED = "Either Password or OTP is required."  # noqa: S105
    PASSWORD_CHANGE_REMINDER = "Password is older than 30 days, please change it now."  # noqa: S105
    MFA_SETUP_SUCCESS = "MFA setup successfully"
    MFA_VERIFIED = "MFA verified successfully"
    MFA_ENABLED = "MFA enabled successfully"
    MFA_DISABLED = "MFA disabled successfully"
    PASSWORD_REMINDER_MONTHLY = "Your password needs to be changed every 30 days."  # noqa: S105


class UserAuthAction(StrEnum):
    MFA_VERIFY = "mfa_verify"
    MFA_SETUP = "mfa_setup"
    CHANGE_PASSWORD = "change_password"  # noqa: S105


class UserRedisKeys:
    """Utility class for user-related Redis keys."""

    SESSION_KEY_TEMPLATE = "sessions:{tenant_id}:{app_id}:{user_id}:{session_id}"

    @classmethod
    def session_key(
        cls, tenant_id: int, app_id: int, user_id: int, session_id: str
    ) -> str:
        return cls.SESSION_KEY_TEMPLATE.format(
            tenant_id=tenant_id, app_id=app_id, user_id=user_id, session_id=session_id
        )

    SCOPES_KEY_TEMPLATE = "scopes:{tenant_id}:{app_id}:{user_id}"

    @classmethod
    def scopes_key(cls, tenant_id: int, app_id: int, user_id: int) -> str:
        return cls.SCOPES_KEY_TEMPLATE.format(
            tenant_id=tenant_id, app_id=app_id, user_id=user_id
        )

    LOGIN_OTP_HASHED_KEY_TEMPLATE = "login_otp:{hashed_key}"

    @classmethod
    def login_otp_key(cls, hashed_user_ulid: str) -> str:
        return cls.LOGIN_OTP_HASHED_KEY_TEMPLATE.format(hashed_key=hashed_user_ulid)

    LOGIN_THROTTLE_KEY_TEMPLATE = "login_throttle:{hashed_key}"

    @classmethod
    def login_throttle_key(cls, hashed_user_ulid: str) -> str:
        return cls.LOGIN_THROTTLE_KEY_TEMPLATE.format(hashed_key=hashed_user_ulid)

    LOGIN_LOCKOUT_ATTEMPTS_KEY_TEMPLATE = "login_lockout_attempts:{hashed_key}"

    @classmethod
    def login_lockout_attempts_key(cls, hashed_user_ulid: str) -> str:
        return cls.LOGIN_LOCKOUT_ATTEMPTS_KEY_TEMPLATE.format(
            hashed_key=hashed_user_ulid
        )

    LOGIN_LOCKOUT_KEY_TEMPLATE = "login_lockout:{hashed_key}"

    @classmethod
    def login_lockout_key(cls, hashed_user_ulid: str) -> str:
        return cls.LOGIN_LOCKOUT_KEY_TEMPLATE.format(hashed_key=hashed_user_ulid)


class UserDefaults:
    REDIS_USER_SCOPES_TTL = 86400  # in seconds, 1 day
    PASSWORD_REMINDER_TOKEN_EXPIRE = 15  # in minutes
