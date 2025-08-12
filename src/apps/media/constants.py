from enum import StrEnum


class MediaType(StrEnum):
    """Enum for media type"""

    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    UNKNOWN = "UNKNOWN"