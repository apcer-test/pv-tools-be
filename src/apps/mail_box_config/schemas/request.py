from pydantic import model_validator

from core.common_helpers import validate_string_fields
from core.types import FrequencyType, Providers
from core.utils.schema import CamelCaseModel


class CreateUpdateMailBoxConfigRequest(CamelCaseModel):
    """This class represents the request body for creating or updating a mail box configuration."""

    recipient_email: str
    app_password: str
    provider: Providers
    frequency: FrequencyType





class EncryptedRequest(CamelCaseModel):
    """
    request model for encrypted data
    """

    encrypted_data: str
    encrypted_key: str
    iv: str

    _validate_string_fields = model_validator(mode="before")(validate_string_fields)
