import httpx

from apps.mail_box_config.exceptions import InvalidTokenException
from config import settings
from constants.messages import (
    ACCESS_TOKEN_GRANT_TYPE,
    ACCESS_TOKEN_SCOPE,
    CONTENT_TYPE,
    GRANT_TYPE,
    REFRESH_TOKEN_SCOPE,
)


async def generate_refresh_token(
    app_password: str,
    microsoft_client_id: str,
    redirect_uri: str,
    client_secret: str,
    refresh_token_validity_days: int,
) -> str:
    """Function to generate refresh token using app password
    :param app_password: app password of the user
    :param user_id: user id of the user
    :param client_id: client id of the user
    :param redirect_uri: redirect uri of the user
    :param client_secret: client secret of the user
    :return: refresh token
    """
    base_url = settings.MICROSOFT_BASE_URL
    url = f"{base_url}/common/oauth2/v2.0/token"
    print(url)
    headers = {"Content-Type": CONTENT_TYPE}
    data = {
        "client_id": microsoft_client_id,
        "scope": REFRESH_TOKEN_SCOPE,
        "code": app_password,
        "grant_type": GRANT_TYPE,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    if url is None:
        raise ValueError("URL cannot be None")

    try:
        response = httpx.post(url, headers=headers, data=data)  # nosec B113
        response.raise_for_status()
        response_data = response.json()
        refresh_token = response_data.get("refresh_token")
        if not refresh_token:
            raise InvalidTokenException(
                f"Refresh token not found in response: {response_data}"
            )
        return refresh_token
    except httpx.HTTPStatusError as e:
        # HTTP error occurred
        error_detail = ""
        try:
            error_detail = e.response.json()
        except Exception:
            error_detail = e.response.text if e.response else str(e)
        raise InvalidTokenException(
            f"HTTP error: {e.response.status_code if e.response else 'N/A'} - {error_detail}"
        )
    except Exception as e:
        raise InvalidTokenException(
            f"An error occurred while generating refresh token: {str(e)}"
        )


def generate_access_token(
    password: str, microsoft_client_id: str, client_secret: str
) -> str:
    """Function to generate access token using refresh token"""
    headers = {"Content-Type": CONTENT_TYPE}
    base_url = settings.MICROSOFT_BASE_URL
    url = f"{base_url}/common/oauth2/v2.0/token"
    input_data = {
        "client_id": microsoft_client_id,
        "scope": ACCESS_TOKEN_SCOPE,
        "refresh_token": f"{password}",
        "grant_type": ACCESS_TOKEN_GRANT_TYPE,
        "client_secret": client_secret,
    }
    print(url)

    response = httpx.post(url, headers=headers, data=input_data)  # nosec B113

    data = response.json()

    return data["access_token"]
