from pydantic import BaseModel, ValidationInfo, field_validator

from apps.master_modules.exception import InvalidRequestException, MaxLengthException
from constants.config import NAME_MAX_LENGTH, R2_R3_MAX_LENGTH


class CodeListLookupValueCreateRequest(BaseModel):
    """
    Request schema for creating a code-list lookup value
    """

    name: str
    e2b_code_r2: str | None = None
    e2b_code_r3: str | None = None

    @field_validator("name", "e2b_code_r2", "e2b_code_r3")
    @classmethod
    def _validate_fields(cls, value: str | None, info: ValidationInfo) -> str | None:
        """Validate the fields of the request."""
        if info.field_name == "name":
            if value is None or (isinstance(value, str) and value.strip() == ""):
                raise InvalidRequestException
            if value is not None and len(value) > NAME_MAX_LENGTH:
                raise MaxLengthException
        elif info.field_name in ("e2b_code_r2", "e2b_code_r3"):
            if value is not None and len(value) > R2_R3_MAX_LENGTH:
                raise MaxLengthException
        return value


class NFListLookupValueCreateRequest(BaseModel):
    """
    Request schema for creating an nf-list lookup value
    """

    name: str

    @field_validator("name")
    @classmethod
    def _name_validate(cls, value: str) -> str:
        """Validate the name field of the request."""
        if value is None or value.strip() == "":
            raise InvalidRequestException
        if len(value) > NAME_MAX_LENGTH:
            raise MaxLengthException
        return value


class UpdateLookupValueStatusRequest(BaseModel):
    """
    Request schema to update is_active for a lookup value.
    """

    is_active: bool


class LookupValuesBySlugsRequest(BaseModel):
    """
    Request schema to fetch lookup values by a list of lookup slugs.
    """

    slugs: list[str]


class UpdateLookupValueRequest(BaseModel):
    """
    Partial update schema for a lookup value. All fields are optional.
    For nf-list values, only `name` and `is_active` are allowed.
    For code-list values, `e2b_code_r2` and `e2b_code_r3` may also be provided.
    """

    name: str | None = None
    e2b_code_r2: str | None = None
    e2b_code_r3: str | None = None
    is_active: bool | None = None

    @field_validator("name", "e2b_code_r2", "e2b_code_r3")
    @classmethod
    def _validate_fields(cls, value: str | None, info: ValidationInfo) -> str | None:
        """
        Validate the fields of the request.
        """
        if value is None:
            return value

        if info.field_name == "name":
            if value.strip() == "":
                raise InvalidRequestException
            if len(value) > NAME_MAX_LENGTH:
                raise MaxLengthException
        elif info.field_name in ("e2b_code_r2", "e2b_code_r3"):
            if len(value) > R2_R3_MAX_LENGTH:
                raise MaxLengthException

        return value
