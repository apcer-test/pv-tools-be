from core.utils.schema import CamelCaseModel


class LookupResponse(CamelCaseModel):
    """Lookup response model."""

    id: str
    name: str
    slug: str


class CodeListLookupValueResponse(CamelCaseModel):
    """Code list lookup value response model."""

    id: str
    name: str
    e2b_code_r2: str | None = None
    e2b_code_r3: str | None = None
    is_active: bool


class NFListLookupValueResponse(CamelCaseModel):
    """NF list lookup value response model."""

    id: str
    name: str
    is_active: bool
