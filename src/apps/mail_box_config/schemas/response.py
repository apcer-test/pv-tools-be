from datetime import date, datetime

from pydantic import EmailStr, field_serializer

from core.types import FrequencyType
from core.utils.schema import CamelCaseModel


class CreateUpdateMailBoxConfigResponse(CamelCaseModel):
    """This class represents the response data for creating or updating a user configuration."""

    id: str
    recipient_email: EmailStr
    app_password: str
    start_date: date | None = None
    end_date: date | None = None
    frequency: FrequencyType

    @field_serializer("start_date", "end_date")
    def serialize_dates(self, value: date | None) -> str | None:
        """Serialize the start_date and end_date fields to a string in the format "dd-mm-yyyy".

        Args:
            value (date | None): The date value to be serialized.

        Returns:
            str | None: The serialized date string or None if the value is None.
        """
        if value:
            return value.strftime("%d-%m-%Y")
        return None


class MailBoxConfigResponse(CamelCaseModel):
    """This class represents the response data for retrieving a user."""

    id: str
    recipient_email: EmailStr | None = None
    app_password: str | None = None
    frequency: FrequencyType | None = (None,)
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime | None = None

    @field_serializer("start_date", "end_date")
    def serialize_dates(self, value: date | None) -> str | None:
        """Serialize the start_date and end_date fields to a string in the format "dd-mm-yyyy".

        Args:
            value (date | None): The date value to be serialized.

        Returns:
            str | None: The serialized date string or None if the value is None.
        """
        if value:
            return value.strftime("%d-%m-%Y")
        return None


class BaseMailBoxPollingConfigResponse(CamelCaseModel):
    """This is the base class for the mail box polling configuration response.

    Attributes:
        id (UUID): The unique identifier for the bank configuration.
        bank_email (str): The email address associated with the bank.
        name (str): The name of the bank.
        subject_line (str): The subject line used in communications.
        frequency (FrequencyType): The frequency of the bank configuration updates.
    """

    id: str
    company_email: str
    subject_line: str | None = None
