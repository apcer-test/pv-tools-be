from authlib.integrations.starlette_client import OAuth

from config import settings
from core.types import Providers


class SSOOAuthClient:
    """
    OAuth client for Single Sign-On (SSO) integration with various providers.
    This class initializes an OAuth client for integrating with different identity providers for SSO.
    The supported providers include Google, Facebook, and Microsoft, each configured with specific settings.
    Args:
        provider (Providers): The identity provider to configure the OAuth client for.
    Attributes:
        oauth (OAuth): The OAuth client instance.
        provider (Providers): The identity provider associated with the OAuth client.
    Example Usage:
        To create an OAuth client for Google:
        ```
        google_client = SSOOAuthClient(Providers.GOOGLE)
        ```
    """

    def __init__(self, provider):
        self.oauth = OAuth()
        self.provider = provider

        match self.provider:

            case Providers.MICROSOFT:
                self.oauth.register(
                    self.provider,
                    client_id=settings.MICROSOFT_CLIENT_ID,
                    client_secret=settings.MICROSOFT_CLIENT_SECRET,
                    server_metadata_url=settings.MICROSOFT_METADATA_URL,
                    client_kwargs={"scope": settings.MICROSOFT_SCOPE},
                )
