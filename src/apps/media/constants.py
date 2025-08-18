from enum import StrEnum


class MediaType(StrEnum):
    """Enum for media type"""

    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    UNKNOWN = "UNKNOWN"

image_extensions = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif"
    ".bmp",
    ".svg",
    ".webp",
    ".heic"
]

document_extensions = [
    ".pdf",
    ".doc",
    ".docx",
    ".txt"
    ".rtf",
    ".odt"
]