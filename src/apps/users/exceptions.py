import constants
from apps.users.constants import UserErrorMessage, UserMessage
from core.exceptions import (
    AlreadyExistsError,
    BadRequestError,
    CustomException,
    NotFoundError,
    UnauthorizedError,
    UnprocessableEntityError,
)


class UserNotFoundError(NotFoundError):
    """User not found."""

    message: str = UserErrorMessage.USER_NOT_FOUND


class PasswordEmptyError(BadRequestError):
    """Password empty."""

    message: str = UserErrorMessage.PASSWORD_EMPTY


class LockAccountError(UnauthorizedError):
    """Lock account temporary."""

    message: str = UserErrorMessage.ACCOUNT_LOCKED


class InvalidCredentialsError(UnauthorizedError):
    """Custom exception to show a generic error message."""

    message = UserErrorMessage.INVALID_CREDS


class AccountAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create an account that already exists."""

    message = UserMessage.ACCOUNT_ALREADY_EXISTS


class PhoneAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a Phone number already exists."""

    message = UserMessage.PHONE_NUMER_EXISTS


class GeneratePasswordError(UnprocessableEntityError):
    """ """

    message = UserMessage.GENERATE_PASSWORD


class UserNameAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a username already exists."""

    message = UserMessage.USERNAME_EXISTS


class EmailAlreadyExistsError(AlreadyExistsError):
    """Exception raised when attempting to create a email already exists."""

    message = UserMessage.EMAIL_EXISTS


class PasswordNotMatchError(BadRequestError):
    """Password not match."""

    message: str = UserMessage.PASSWORD_NOT_MATCH


class WeakPasswordError(BadRequestError):
    """Weak Password."""

    message: str = UserMessage.WEAK_PASSWORD


class PasswordMatchedError(BadRequestError):
    """Matched Recent Password."""

    message: str = UserMessage.RECENT_PASSWORD_MATCHED


class InvalidPasswordError(BadRequestError):
    """Invalid Current Password."""

    message: str = UserMessage.INVALID_PASSWORD


class InvalidPhoneNumberError(BadRequestError):
    """Invalid Phone Number."""

    message: str = UserMessage.INVALID_PHONE_NUMBER


class PhoneRequiredError(BadRequestError):
    """Phone number is required."""

    message: str = UserMessage.PHONE_REQUIRED


class PhoneOrEmailRequiredError(BadRequestError):
    """Either phone or email is required."""

    message: str = UserMessage.PHONE_OR_EMAIL_REQUIRED


class PasswordOrOTPRequiredError(BadRequestError):
    """Either password or OTP is required."""

    message: str = UserMessage.PASSWORD_OR_OTP_REQUIRED


class PasswordChangeReminderError(BadRequestError):
    """Password expired."""

    message: str = UserMessage.PASSWORD_CHANGE_REMINDER


class UserAlreadyMFEnrolledError(AlreadyExistsError):
    """User already has MFA enrolled."""

    message: str = UserErrorMessage.USER_ALREADY_MFA_ENROLLED


class UserMFANotSetupError(BadRequestError):
    """User MFA not setup."""

    message: str = UserErrorMessage.MFA_NOT_SETUP


class UserMfaCodeRequiredError(UnprocessableEntityError):
    """User MFA OTP required."""

    message: str = UserErrorMessage.MFA_CODE_REQUIRED


class UserMfaNotDisableError(UnprocessableEntityError):
    """User MFA not disable."""

    message: str = UserErrorMessage.MFA_NOT_DISABLE


class DuplicateEmailException(CustomException):
    """
    Custom exception for email duplication.
    """

    message = constants.DUPLICATE_EMAIL


class InvalidCredentialsException(UnauthorizedError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.INVALID_CREDS


class UserNotFoundException(NotFoundError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.USER_NOT_FOUND


class EmptyDescriptionException(UnprocessableEntityError):
    """
    Custom exception for issue with the notes create empty description.
    """

    message = constants.DESCRIPTION


class InvalidEncryptedData(BadRequestError):
    """
    Custom exception for User already assigned error.
    """

    message = constants.INVALID_ENCRYPTED_DATA


class WeakPasswordException(BadRequestError):
    """
    Custom exception for User already assigned error.
    """

    message = constants.WEAK_PASSWORD


class InvalidPhoneFormatException(BadRequestError):
    """
    Custom exception for invalid phone number format.
    """

    message = constants.INVALID_PHONE_NUMBER


class InvalidEmailException(BadRequestError):
    """
    Custom exception for invalid email.
    """

    message = constants.INVALID_EMAIL


class InvalidRequestException(BadRequestError):
    """
    Custom exception for invalid request.
    """

    message = constants.INVALID_REQUEST


class EmailNotFoundError(BadRequestError):
    """
    Custom exception for email not found.
    """

    message = constants.EMAIL_NOT_FOUND