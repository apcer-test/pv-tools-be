from typing import Optional

from pydantic import BaseModel


class MeddraVersion(BaseModel):
    """
    Response schema for MedDRA version.
    """

    version_id: int
    version_name: str
    release_date: str  # ISO date string per sample ("YYYY-MM-DD")
    database: Optional[str] = None


class MeddraTerm(BaseModel):
    """
    Response schema for MedDRA term.
    """

    # Fields as returned by the API (allowing nulls)
    version_id: Optional[int] = None
    level: Optional[str] = None  # "LLT"|"PT"|"HLGT"|"HLT"|"SOC"
    levelcode: Optional[str] = None
    term: Optional[str] = None  # e.g., "Hallucination gustatory 10019065"
    soctype: Optional[str] = None  # sometimes null in response
    isprimary: Optional[bool] = None
    parentlevelcode: Optional[str] = None
    database: Optional[str] = None


class MeddraDetailNode(BaseModel):
    """
    Response schema for MedDRA detail node.
    """

    version_id: Optional[int] = None
    level: str
    levelcode: Optional[str] = None
    term: str
    soctype: Optional[str] = None
    # provider sometimes returns "Y    " -> keep as string tolerant
    isprimary: Optional[bool | str] = None
    parentlevelcode: Optional[str] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    lstchild: Optional[list["MeddraDetailNode"]] = None


MeddraDetailNode.model_rebuild()  # for forward refs
