from enum import IntEnum, StrEnum


class AICBURLs(StrEnum):
    """
    URLs for MedDRA endpoints in AiCloudBase.
    """

    MEDDRA_VERSION_LIST = "/api/externalmeddra/meddra-versionlist"
    MEDDRA_LIST_SEARCH = "/api/externalmeddra/MedDRAListSearch"
    MEDDRA_DETAIL_SEARCH = "/api/externalmeddra/MedDRADetailSearch"


class AICBTimeouts(IntEnum):
    """
    Timeouts for MedDRA endpoints in AiCloudBase.
    """

    MEDDRA_VERSION_LIST = 5.0
    MEDDRA_LIST_SEARCH = 5.0
    MEDDRA_DETAIL_SEARCH = 5.0
