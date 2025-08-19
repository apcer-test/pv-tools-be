import base64
import hashlib
import hmac

from passlib.context import CryptContext

from apps.users.exceptions import InvalidCredentialsError
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password: str) -> str:
    """
    Hash a password.

    Args:
        password (str): The password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def verify_hash(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


class Hash:
    """
    Class for all password related operations.
    """

    secret_key = bytes(settings.JWT_SECRET_KEY, "utf-8")

    @classmethod
    def make(cls, string: str):
        """
        Method to hash the given string.

        :param string: The string to be hashed
        :return: Hashed version of the string.
        """

        if string is None:
            raise InvalidCredentialsError

        hash_ = hmac.new(cls.secret_key, bytes(string, "utf-8"), hashlib.sha256)
        hash_.hexdigest()
        hash_result = base64.b64encode(hash_.digest()).decode("utf-8")
        return hash_result

    @classmethod
    def verify(cls, hashed: str, raw: str) -> bool:
        """
        Method to verify the hash of the given string.

        :param hashed: The hashed string.
        :param raw: The string to be verified.
        :return: True if hash matches the given string, False otherwise.
        """
        if not isinstance(raw, str):
            raise InvalidCredentialsError
        return cls.make(raw) == hashed
