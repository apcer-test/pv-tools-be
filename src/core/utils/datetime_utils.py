from datetime import datetime, timedelta
from enum import Enum, StrEnum
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")


class TimeInterval(Enum):
    """Enum for time intervals in seconds."""

    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    WEEK = 604800


class DateFormat(StrEnum):
    """Enum for date formats."""

    # Standard format
    STANDARD = "%Y-%m-%d %H:%M:%S"

    # Date only
    DATE_ONLY = "%Y-%m-%d"

    # Time only
    TIME_ONLY = "%H:%M:%S"

    # ISO format
    ISO = "%Y-%m-%dT%H:%M:%S"

    # ISO with timezone
    ISO_WITH_TZ = "%Y-%m-%dT%H:%M:%S%z"

    # RFC 3339 format
    RFC3339 = "%Y-%m-%dT%H:%M:%S.%fZ"


def get_utc_now() -> datetime:
    """Get current UTC datetime without timezone info."""
    return datetime.now(UTC).replace(tzinfo=None)


def format_datetime(dt: datetime, date_format: str = DateFormat.STANDARD.value) -> str:
    """
    Format datetime object to string.

    Args:
        dt: datetime object to format
        date_format: format string (default: "%Y-%m-%d %H:%M:%S")

    Returns:
        Formatted datetime string
    """
    return dt.strftime(date_format)


def parse_datetime(
    date_str: str, date_format: str = DateFormat.STANDARD.value
) -> datetime:
    """
    Parse string to datetime object.

    Args:
        date_str: string to parse
        date_format: format string (default: "%Y-%m-%d %H:%M:%S")

    Returns:
        Parsed datetime object
    """
    # Use fromisoformat for ISO formats
    if date_format in [
        DateFormat.ISO.value,
        DateFormat.ISO_WITH_TZ.value,
        DateFormat.RFC3339.value,
    ]:
        dt = datetime.fromisoformat(date_str)
        # Convert to UTC if timezone is present
        if dt.tzinfo:
            return dt.astimezone(UTC).replace(tzinfo=None)
        return dt

    # For other formats, use strptime
    dt = datetime.strptime(date_str, date_format)  # noqa: DTZ007
    # Convert to UTC if timezone is present
    if dt.tzinfo:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def convert_to_utc(dt: datetime) -> datetime:
    """
    Convert datetime to UTC without timezone info.

    Args:
        dt: datetime object to convert

    Returns:
        UTC datetime without timezone info
    """
    if dt.tzinfo:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def add_to_datetime(
    dt: datetime,
    years: int = 0,
    months: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    *,
    to_utc: bool = False,
) -> datetime:
    """
    Add time units to a datetime object.

    Args:
        dt: datetime object to modify
        years: number of years to add
        months: number of months to add
        days: number of days to add
        hours: number of hours to add
        minutes: number of minutes to add
        seconds: number of seconds to add

    Returns:
        Modified datetime object with added time units
    """
    # Handle month/year overflow
    total_month = dt.month + months
    new_year = dt.year + years + (total_month - 1) // 12
    new_month = (total_month - 1) % 12 + 1

    # Adjust the day safely (e.g., Feb 30 → Feb 28/29)
    # First, find the last valid day of the new month
    def last_day_of_month(year: int, month: int) -> int:
        if month == 2:
            is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
            return 29 if is_leap else 28
        return [31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 30, 31][month - 1]

    new_day = min(dt.day, last_day_of_month(new_year, new_month))

    # Create the updated datetime with safe date
    updated_dt = dt.replace(year=new_year, month=new_month, day=new_day)

    # Add remaining time components
    updated_dt += timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    # Convert to UTC if requested (strip tzinfo to keep it naive)
    if to_utc and updated_dt.tzinfo:
        updated_dt = updated_dt.astimezone(UTC).replace(tzinfo=None)

    return updated_dt


def get_human_readable_time_ago(dt: datetime) -> str:
    """
    Get human-readable time difference from now.

    Args:
        dt: datetime to compare with now

    Returns:
        Human-readable time difference (e.g., "2 hours ago", "1 day ago")
    """
    now = get_utc_now()
    diff = now - dt

    if diff.total_seconds() < TimeInterval.MINUTE.value:
        return f"{int(diff.total_seconds())} seconds ago"
    if diff.total_seconds() < TimeInterval.HOUR.value:
        return f"{int(diff.total_seconds() // TimeInterval.MINUTE.value)} minutes ago"
    if diff.total_seconds() < TimeInterval.DAY.value:
        return f"{int(diff.total_seconds() // TimeInterval.HOUR.value)} hours ago"
    if diff.total_seconds() < TimeInterval.WEEK.value:
        return f"{int(diff.total_seconds() // TimeInterval.DAY.value)} days ago"
    return f"{int(diff.total_seconds() // TimeInterval.WEEK.value)} weeks ago"
