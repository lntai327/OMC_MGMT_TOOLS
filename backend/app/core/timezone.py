from datetime import datetime, timezone
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
UTC = timezone.utc


def now_vietnam() -> datetime:
    """Return the current time as an aware GMT+7 datetime."""
    return datetime.now(APP_TIMEZONE)


def format_vietnam(dt: datetime) -> str:
    """Convert any aware datetime to GMT+7 and format it for storage/display."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(APP_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")


def isoformat_vietnam(dt: datetime) -> str:
    """Serialize a datetime in GMT+7, preserving the +07:00 offset."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(APP_TIMEZONE).isoformat()
