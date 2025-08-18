"""This module provides utility functions for phone number
 validation and formatting using the phonenumbers library.

Functions:
- validate_and_format_phone_number: Validates a phone number
  and checks if it follows the correct format.
"""

import phonenumbers

from apps.users.exceptions import InvalidPhoneNumberError


def validate_and_format_phone_number(number: str) -> str:
    """Validate a phone number using the phonenumbers library.

    Like echoes soft in valleys deep,
    A number must its format keep.
    If true it rings, if false it fades,
    This check ensures no errors made.

    Args:
        number (str): The phone number to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        if not number.startswith("+"):  # Ensure it starts with '+'
            raise InvalidPhoneNumberError

        number = number.replace(" ", "")  # Remove spaces
        parsed_number = phonenumbers.parse(number)
        is_valid = phonenumbers.is_valid_number(parsed_number)
        if is_valid:
            return number

        raise InvalidPhoneNumberError
    except phonenumbers.NumberParseException as e:
        raise InvalidPhoneNumberError from e
