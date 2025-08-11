import constants
from core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError


class ExistingLookupValueException(AlreadyExistsError):
    """Exception raised when a lookup value already exists."""

    message = constants.LOOKUP_VALUE_ALREADY_EXISTS


class LookupNotFoundException(NotFoundError):
    """Exception raised when a lookup is not found."""

    message = constants.LOOKUP_NOT_FOUND


class LookupValueNotFoundException(NotFoundError):
    """Exception raised when a lookup value is not found."""

    message = constants.LOOKUP_VALUE_NOT_FOUND


class InvalidFileFormatException(BadRequestError):
    """Exception raised when an invalid file format is provided."""

    message = constants.INVALID_FILE_FORMAT


class InvalidExcelSheetDataException(BadRequestError):
    """Exception raised when an invalid excel sheet data is provided."""

    message = constants.INVALID_EXCEL_SHEET_DATA


class EmptyExcelFileException(BadRequestError):
    """Exception raised when an empty excel file is provided."""

    message = constants.EMPTY_EXCEL_FILE


class MaxLengthException(BadRequestError):
    """Exception raised when a value exceeds the maximum length."""

    message = constants.MAX_LENGTH_EXCEEDED


class InvalidRequestException(BadRequestError):
    """Exception raised when an invalid request is provided."""

    message = constants.INVALID_REQUEST
