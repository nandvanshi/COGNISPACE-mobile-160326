"""
Date Utilities - Centralized IST/UTC date handling for COGNISPACE.
Prevents recurring timezone bugs in scheduled jobs and queries.
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def get_ist_today_range_utc():
    """
    Get today's date range in IST, converted to UTC for database queries.
    
    Returns:
        tuple: (start_utc, end_utc, display_date_str, display_date_long)
            - start_utc: datetime - Start of today IST in UTC
            - end_utc: datetime - End of today IST in UTC  
            - display_date_str: str - "28/03/2026" format for emails
            - display_date_long: str - "28 March 2026" format for WhatsApp
    """
    now_ist = datetime.now(IST)
    today_start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end_ist = today_start_ist + timedelta(days=1)
    
    start_utc = today_start_ist.astimezone(timezone.utc)
    end_utc = today_end_ist.astimezone(timezone.utc)
    
    display_date_str = today_start_ist.strftime("%d/%m/%Y")
    display_date_long = today_start_ist.strftime("%d %B %Y")
    
    return start_utc, end_utc, display_date_str, display_date_long


def utc_range_query_strings(start_utc, end_utc):
    """
    Format UTC datetime range for MongoDB string queries.
    Uses .isoformat() to match the storage format (includes +00:00 suffix).
    
    Args:
        start_utc: datetime with UTC tzinfo
        end_utc: datetime with UTC tzinfo
    
    Returns:
        tuple: (start_str, end_str) - ISO format strings matching DB storage format
    """
    # Ensure both are UTC
    if start_utc.tzinfo is None:
        start_utc = start_utc.replace(tzinfo=timezone.utc)
    if end_utc.tzinfo is None:
        end_utc = end_utc.replace(tzinfo=timezone.utc)
    
    return start_utc.isoformat(), end_utc.isoformat()


def format_time_ist(dt_str):
    """
    Convert an ISO datetime string (stored in UTC) to IST time display.
    
    Args:
        dt_str: ISO datetime string (e.g., "2026-03-28T04:30:00+00:00")
    
    Returns:
        str: Time in IST format (e.g., "10:00 AM")
    """
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        ist_dt = dt.astimezone(IST)
        return ist_dt.strftime("%I:%M %p")
    except (ValueError, AttributeError):
        return "N/A"


def format_datetime_ist(dt_str):
    """
    Convert an ISO datetime string to IST date and time strings.
    
    Returns:
        tuple: (date_str, time_str) - e.g., ("28/03/2026", "10:00 AM")
    """
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        ist_dt = dt.astimezone(IST)
        return ist_dt.strftime("%d/%m/%Y"), ist_dt.strftime("%I:%M %p")
    except (ValueError, AttributeError):
        return "N/A", "N/A"


def get_past_days_utc(days):
    """
    Get UTC datetime for N days ago from current IST time.
    
    Args:
        days: Number of days in the past
    
    Returns:
        str: ISO format UTC string
    """
    now_ist = datetime.now(IST)
    past_ist = now_ist - timedelta(days=days)
    past_utc = past_ist.astimezone(timezone.utc)
    return past_utc.isoformat()
