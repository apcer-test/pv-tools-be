import base64
import json
import secrets

from cryptography.fernet import Fernet

from config import settings


class CryptoUtil:
    """
    Utility class for cryptography encryption and decryption.
    Uses the FERNET_KEY from environment/config.
    """

    def __init__(self, key: str | None = None) -> None:
        if key is None:
            key = settings.FERNET_KEY
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return the encrypted token as a string."""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Decrypt a Fernet token string and return the original string.
        Raises InvalidToken if the token is invalid or corrupted.
        """
        return self.fernet.decrypt(token.encode()).decode()

    def generate_secret_key(self, length: int = 20) -> str:
        """
        Generate a random Base32-encoded secret key, stripped of padding.
        """
        random_bytes = secrets.token_bytes(length)
        return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")

    def generate_backup_codes(
        self, num_codes: int = 5, code_length: int = 20
    ) -> list[str]:
        """
        Generate a list of secure random backup codes.
        """
        return [secrets.token_urlsafe(code_length) for _ in range(num_codes)]

    def encrypt_backup_codes(self, codes: list) -> str:
        """
        Encrypt the backup codes list and return as a base64-encoded encrypted string.
        """
        codes_json = json.dumps(codes)
        encrypted = self.fernet.encrypt(codes_json.encode("utf-8"))

        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    def decrypt_backup_codes(self, encrypted_codes: str) -> list[str]:
        """
        Decrypt the encrypted backup codes and return the list.

        Raises:
            InvalidToken: If the encrypted data is invalid or tampered.
        """
        encrypted_codes_bytes = base64.urlsafe_b64decode(encrypted_codes)
        decrypted = self.fernet.decrypt(encrypted_codes_bytes)

        return json.loads(decrypted.decode("utf-8"))
