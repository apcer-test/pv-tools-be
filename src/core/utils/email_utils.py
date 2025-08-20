from datetime import UTC, datetime
from typing import Any

import httpx

from config import settings
from constants.config import ALLOWED_ATTACHMENT_EXTENSIONS, OUTLOOK_PAGE_SIZE
from constants.messages import DATE_TIME_FORMAT
from core.utils import logger
from core.utils.microsoft_oauth_util import generate_access_token


def build_outlook_filter(last_execution_date: datetime | None = None) -> str:
    """Build filter for Outlook API to fetch emails based on configuration.

    Args:
        last_execution_date: Optional datetime to filter emails after this date

    Returns:
        str: Microsoft Graph API filter string
    """
    # Initialize filters list with no attachment restriction
    filters = []

    # Add date filter if provided
    if last_execution_date:
        date_str = last_execution_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        filters.append(f"receivedDateTime ge {date_str}")

    # Return the combined filters or a default filter that matches all emails
    return " and ".join(filters) if filters else "1 eq 1"


def fetch_email_outlook(
    microsoft_client_id: str,
    client_secret: str,
    password: str,
    last_execution_date: datetime | None = None,
    additional_filter: str | None = None,
    app_password_expiry: datetime | None = None,
) -> list[dict[str, Any]]:
    """Fetch emails from Outlook based on configured filters.

    Args:
        microsoft_client_id: Microsoft app client ID
        client_secret: Microsoft app client secret
        password: App password/refresh token
        last_execution_date: Optional datetime to filter emails after this date
        additional_filter: Optional additional filter string
        app_password_expiry: Optional expiry datetime for app password

    Returns:
        list[dict]: List of matching emails with attachments
    """
    try:
        if app_password_expiry and app_password_expiry < datetime.now(UTC).replace(
            tzinfo=None
        ):
            logger.warning("Refresh token expired for user")
            return []

        access_token = generate_access_token(
            password, microsoft_client_id, client_secret
        )

        url = f"{settings.MICROSOFT_GRAPH_URL}/mailFolders/Inbox/messages"

        # Use either additional_filter or build filter from config
        if additional_filter:
            params = {"$filter": additional_filter, "$top": OUTLOOK_PAGE_SIZE}
        else:
            filter_string = build_outlook_filter(
                last_execution_date=last_execution_date
            )
            params = {"$filter": filter_string, "$top": OUTLOOK_PAGE_SIZE}

        headers = {"Authorization": f"Bearer {access_token}"}
        matching_emails = []

        while url:
            response = httpx.get(url, params=params, headers=headers)
            data = response.json()

            for email in data["value"]:
                # Get email metadata
                email_id = email["id"]
                from_address = email["from"]["emailAddress"]["address"]
                received_date = datetime.strptime(
                    email["receivedDateTime"], DATE_TIME_FORMAT
                ).replace(tzinfo=None)

                # Skip old emails if last_execution_date is set
                if last_execution_date and received_date <= last_execution_date:
                    continue

                # Initialize attachment data
                email_attachments = []
                attachment_names = []

                # Process attachments if present
                if email.get("hasAttachments"):
                    # Get attachments
                    attachments_url = (
                        f"{settings.MICROSOFT_GRAPH_URL}/messages/{email_id}/attachments"
                    )
                    attachments_response = httpx.get(attachments_url, headers=headers)
                    attachments = attachments_response.json()["value"]

                    # Process attachments
                    for attachment in attachments:
                        file_name = attachment["name"]
                        if (
                            file_name.split(".")[-1].lower()
                            in ALLOWED_ATTACHMENT_EXTENSIONS
                        ):
                            content_url = f"{settings.MICROSOFT_GRAPH_URL}/messages/{email_id}/attachments/{attachment['id']}/$value"
                            content_response = httpx.get(content_url, headers=headers)
                            email_attachments.append(content_response.content)
                            attachment_names.append(file_name)

                # Add all emails, with or without attachments
                matching_emails.append(
                    {
                        "id": email_id,
                        "from": from_address,
                        "subject": email["subject"],
                        "attachment": email_attachments,
                        "filename": attachment_names,
                        "date": received_date,
                        "body": email.get("body", {}).get("content", ""),
                    }
                )

            # Get next page if available
            url = data.get("@odata.nextLink")

        return matching_emails

    except Exception as e:
        logger.exception(f"Error fetching emails: {e}")
        raise e
