from pydantic import BaseModel


class LookupResponse(BaseModel):
    id: str
    name: str
    slug: str


class CodeListLookupValueResponse(BaseModel):
    id: str
    name: str
    e2b_code_r2: str | None = None
    e2b_code_r3: str | None = None
    is_active: bool


class NFListLookupValueResponse(BaseModel):
    id: str
    name: str
    is_active: bool
