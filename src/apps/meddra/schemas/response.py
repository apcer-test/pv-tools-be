from core.utils.schema import CamelCaseModel


class MeddraVersion(CamelCaseModel):
    """
    Response schema for MedDRA version.
    """

    version_id: int
    version_name: str
    release_date: str  # ISO date string per sample ("YYYY-MM-DD")
    database: str | None = None


class MeddraTerm(CamelCaseModel):
    """
    Response schema for MedDRA term.
    """

    version_id: int | None = None
    level: str
    levelcode: str | None = None
    term: str
    soctype: str | None = None
    isprimary: bool | None = None
    parentlevelcode: str | None = None
    database: str | None = None


class MeddraDetailNode(CamelCaseModel):
    """
    Response schema for MedDRA detail node.
    """

    version_id: int | None = None
    level: str
    levelcode: str | None = None
    term: str
    soctype: str | None = None
    isprimary: bool | str | None = None
    parentlevelcode: str | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    lstchild: list["MeddraDetailNode"] | None = None


MeddraDetailNode.model_rebuild()  # for forward refs
