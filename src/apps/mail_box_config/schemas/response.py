from datetime import date, datetime

from pydantic import EmailStr, field_serializer

from core.types import FrequencyType
from core.utils.schema import CamelCaseModel


class CreateUpdateMailBoxConfigResponse(CamelCaseModel):
    """This class represents the response data for creating or updating a mail box configuration."""

    id: str
    recipient_email: EmailStr
    app_password: str
    frequency: FrequencyType
    app_password_expired_at: datetime | None = None
    last_execution: datetime | None = None


class MailBoxConfigResponse(CamelCaseModel):
    """This class represents the response data for retrieving a mail box configuration."""

    id: str
    recipient_email: EmailStr | None = None
    app_password: str | None = None
    frequency: FrequencyType | None = None
    app_password_expired_at: datetime | None = None
    last_execution: datetime | None = None
    created_at: datetime | None = None



