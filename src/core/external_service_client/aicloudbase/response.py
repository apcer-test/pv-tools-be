from pydantic import BaseModel


class MeddraVersion(BaseModel):
    """
    Response schema for MedDRA version.
    """

    version_id: int
    version_name: str
    release_date: str  # ISO date string per sample ("YYYY-MM-DD")
    database: str | None = None


class MeddraTerm(BaseModel):
    """
    Response schema for MedDRA term.
    """

    # Fields as returned by the API (allowing nulls)
    version_id: int | None = None
    level: str | None = None  # "LLT"|"PT"|"HLGT"|"HLT"|"SOC"
    levelcode: str | None = None
    term: str | None = None  # e.g., "Hallucination gustatory 10019065"
    soctype: str | None = None  # sometimes null in response
    isprimary: bool | None = None
    parentlevelcode: str | None = None
    database: str | None = None


class MeddraDetailNode(BaseModel):
    """
    Response schema for MedDRA detail node.
    """

    version_id: int | None = None
    level: str
    levelcode: str | None = None
    term: str
    soctype: str | None = None
    # provider sometimes returns "Y    " -> keep as string tolerant
    isprimary: bool | str | None = None
    parentlevelcode: str | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    lstchild: list["MeddraDetailNode"] | None = None


MeddraDetailNode.model_rebuild()  # for forward refs
