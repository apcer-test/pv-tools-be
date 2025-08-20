from datetime import datetime

from pydantic import EmailStr

from core.types import FrequencyType
from core.utils.schema import CamelCaseModel


class MailBoxConfigResponse(CamelCaseModel):
    """This class represents the response data for retrieving a mail box configuration."""

    id: str
    recipient_email: EmailStr | None = None
    created_at: datetime | None = None
    is_active: bool | None = None


class MailBoxConfigDetailsResponse(MailBoxConfigResponse):
    """This class represents the response data for retrieving a mail box configuration."""

    frequency: FrequencyType | None = None
    app_password: str | None = None
