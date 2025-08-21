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


class MicrosoftCredentialsResponse(CamelCaseModel):
    """This class represents the response data for retrieving microsoft credentials."""

    client_id: str | None = None
    redirect_uri: str | None = None
    client_secret: str | None = None
    refresh_token_validity_days: int | None = None
    tenant_id: str | None = None
