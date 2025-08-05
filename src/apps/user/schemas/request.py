from core.utils import CamelCaseModel
from pydantic import BaseModel, EmailStr


class EncryptedRequest(CamelCaseModel):
    """
    request model for encrypted data
    """

    encrypted_data: str
    encrypted_key: str
    iv: str


class MicrosoftSSOInitRequest(BaseModel):
    """Schema for initiating Microsoft SSO with email"""
    email: EmailStr
