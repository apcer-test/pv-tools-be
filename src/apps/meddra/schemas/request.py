from pydantic import BaseModel

from core.types import MeddraCondition, MeddraLevel, MeddraOrderBy, MeddraSoctype


class MeddraListSearchRequest(BaseModel):
    """
    Request schema for MedDRA list search.
    """

    version_id: int
    level: MeddraLevel
    levelcode: str | None = None
    term: str | None = None
    condition: MeddraCondition
    orderby: MeddraOrderBy
    soctype: MeddraSoctype
    matchcase: bool


class MeddraDetailSearchRequest(BaseModel):
    """
    Request schema for MedDRA detail search.
    """

    level: MeddraLevel
    levelcode: str
    version_id: int
    soctype: MeddraSoctype
