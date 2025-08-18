from datetime import date

from pydantic import EmailStr, field_validator, model_validator

from apps.mail_box_config.exceptions import EndDateException, StartDateException
from core.common_helpers import validate_string_fields
from core.types import FrequencyType, Providers
from core.utils.schema import CamelCaseModel


class CreateUpdateMailBoxConfigRequest(CamelCaseModel):
    """This class represents the response body for creating a new user."""

    recipient_email: str
    app_password: str
    provider: Providers
    frequency: FrequencyType
    start_date: date
    end_date: date
    company_emails: list[str] = []
    subject_lines: list[str] = []

    @field_validator("start_date")
    def validate_start_date(cls, start_date):
        """Validation for the start date"""
        today = date.today()
        if start_date < date(today.year, today.month, 1):
            raise StartDateException
        return start_date

    @field_validator("end_date")
    def validate_end_date(cls, end_date, values):
        """Validation for end date"""
        start_date = values.data.get("start_date")
        if start_date is None:
            start_date = date.today()
        if end_date < start_date:
            raise EndDateException
        return end_date


class BaseMailBoxPollingConfigRequest(CamelCaseModel):
    """This is the base class for the bank configuration request.

    Attributes:
        bank_email (str): The email address associated with the bank.
        subject_line (str): The subject line used in communications.
        frequency (FrequencyType): The frequency of the bank configuration updates.
        name (str): The name of the bank.
    """

    company_email: EmailStr
    subject_line: str | None = None


class EncryptedRequest(CamelCaseModel):
    """
    request model for encrypted data
    """

    encrypted_data: str
    encrypted_key: str
    iv: str

    _validate_string_fields = model_validator(mode="before")(validate_string_fields)
