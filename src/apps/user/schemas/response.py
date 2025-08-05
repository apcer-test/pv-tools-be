from uuid import UUID

from ulid import ULID

from core.utils import CamelCaseModel


class BaseUserResponse(CamelCaseModel):
    """
    Base response object for user information.

    Attributes:
        id (UUID): The user's unique identifier.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
    """

    id: ULID
    first_name: str
    last_name: str
