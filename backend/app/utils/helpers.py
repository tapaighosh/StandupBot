"""
StandupBot — General Helper Utilities

Common utility functions used across the application.
"""

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    """Get the current UTC timestamp."""
    return datetime.now(timezone.utc)


def today_utc() -> date:
    """Get today's date in UTC."""
    return datetime.now(timezone.utc).date()


def now_in_timezone(tz_name: str) -> datetime:
    """Get the current timestamp in a specific timezone."""
    return datetime.now(ZoneInfo(tz_name))


def today_in_timezone(tz_name: str) -> date:
    """Get today's date in a specific timezone."""
    return now_in_timezone(tz_name).date()


def time_to_datetime(t: time, tz_name: str, for_date: date | None = None) -> datetime:
    """
    Convert a time and timezone to a full datetime.

    Args:
        t: The time of day
        tz_name: IANA timezone name
        for_date: The date to use (defaults to today in the timezone)
    """
    target_date = for_date or today_in_timezone(tz_name)
    tz = ZoneInfo(tz_name)
    return datetime.combine(target_date, t, tzinfo=tz)


def is_within_window(
    current_time: datetime,
    window_start: time,
    window_end: time,
    tz_name: str,
) -> bool:
    """
    Check if the current time falls within a submission window.

    Args:
        current_time: Current datetime (timezone-aware)
        window_start: Window start time
        window_end: Window end time
        tz_name: Team's timezone
    """
    tz = ZoneInfo(tz_name)
    local_time = current_time.astimezone(tz).time()
    return window_start <= local_time <= window_end


def format_response_rate(responded: int, total: int) -> float:
    """Calculate response rate as percentage (0-100)."""
    if total == 0:
        return 0.0
    return round((responded / total) * 100, 1)


BLOCKER_KEYWORDS: list[str] = [
    "blocked",
    "blocker",
    "stuck",
    "waiting on",
    "waiting for",
    "can't proceed",
    "cannot proceed",
    "can't move forward",
    "dependency",
    "held up",
    "need help",
    "need approval",
    "pending review",
    "no access",
]


def detect_blocker_keywords(text: str) -> bool:
    """Check if text contains common blocker keywords."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in BLOCKER_KEYWORDS)
