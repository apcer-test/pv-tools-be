from enum import StrEnum


class RoleType(StrEnum):
    """
    Enumeration of user role types.

    Defines different roles that users can have in the system, including:
    - ADMIN: Administrator role.
    - STAFF: Staff role.
    - USER: Regular user role.
    - ANY: Represents any role.
    - OPTIONAL: Represents an optional role.

    These roles are represented as strings for convenience.

    Attributes:
        ADMIN: Administrator role.
        STAFF: Staff role.
        USER: Regular user role.
        ANY: Represents any role.
        OPTIONAL: Represents an optional role.
    """

    ADMIN = "ADMIN"
    STAFF = "STAFF"
    USER = "USER"
    ANY = "ANY"
    OPTIONAL = "OPTIONAL"


class Providers(StrEnum):
    """
    Enumeration of supported authentication providers.
    """

    MICROSOFT = "microsoft"


class FrequencyType(StrEnum):
    """Enum class of Frequency type"""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    SECONDLY30 = "SECONDLY30"
    SECONDLY60 = "SECONDLY60"


class LookupType(StrEnum):
    """Enum class of Lookup type for master lookups."""

    CODELIST = "code-list"
    NFLIST = "nf-list"


class MeddraLevel(StrEnum):
    """Enum class of MedDRA level"""

    LLT = "LLT"
    PT = "PT"
    HLGT = "HLGT"
    HLT = "HLT"
    SOC = "SOC"


class MeddraCondition(StrEnum):
    """Enum class of MedDRA condition"""

    STARTSWITH = "startswith"
    EXACT = "exact"
    CONTAINS = "contains"


class MeddraOrderBy(StrEnum):
    """Enum class of MedDRA order by"""

    CODE = "Code"
    TERM = "Term"


class MeddraSoctype(StrEnum):
    """Enum class of MedDRA soctype"""

    Y = "Y"
    N = "N"


class LoginActivityStatus(StrEnum):
    """Enum class of Login activity status"""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    LOGOUT = "LOGOUT"
    LOGOUT_FAILED = "LOGOUT_FAILED"
