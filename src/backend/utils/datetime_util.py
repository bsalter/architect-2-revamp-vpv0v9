"""
Datetime utility module for the Interaction Management System.

This module provides functions for managing and manipulating datetime objects,
with specific focus on timezone handling, formatting, validation, and conversion.
These utilities ensure consistent datetime operations across the application.
"""

from datetime import datetime
# pytz version 2023.3
import pytz
# python-dateutil version 2.8.2
from dateutil import parser

from .constants import (
    DEFAULT_TIMEZONE,
    DATETIME_FORMAT,
    DATETIME_FORMAT_WITH_TZ,
    DATE_FORMAT,
    TIME_FORMAT
)
from .enums import Timezone


def validate_datetime_range(start_datetime, end_datetime):
    """
    Validates that end_datetime is after start_datetime.
    
    Args:
        start_datetime (datetime): The start datetime.
        end_datetime (datetime): The end datetime.
        
    Returns:
        bool: True if the range is valid, False otherwise.
    """
    if not isinstance(start_datetime, datetime) or not isinstance(end_datetime, datetime):
        return False
    
    if start_datetime is None or end_datetime is None:
        return False
        
    # Normalize timezones for comparison
    start_utc = get_utc_datetime(start_datetime)
    end_utc = get_utc_datetime(end_datetime)
    
    return end_utc > start_utc


def get_utc_datetime(dt):
    """
    Converts a datetime to UTC timezone.
    
    Args:
        dt (datetime): The datetime to convert.
        
    Returns:
        datetime: Datetime in UTC timezone, or None if input is None.
    """
    if not isinstance(dt, datetime):
        return None
        
    if dt is None:
        return None
        
    if dt.tzinfo is None:
        # Assume UTC for naive datetimes
        return pytz.UTC.localize(dt)
    else:
        # Convert to UTC
        return dt.astimezone(pytz.UTC)


def localize_datetime(dt, timezone_id):
    """
    Localizes a naive datetime to the specified timezone.
    
    Args:
        dt (datetime): The datetime to localize.
        timezone_id (str): The timezone identifier.
        
    Returns:
        datetime: Timezone-aware datetime object.
    """
    if not isinstance(dt, datetime):
        return None
        
    if dt is None:
        return None
        
    # Validate and normalize timezone
    if not Timezone.is_valid(timezone_id):
        timezone_id = DEFAULT_TIMEZONE
        
    tz_id = Timezone.get_iana(timezone_id)
    tz = pytz.timezone(tz_id)
    
    if dt.tzinfo is None:
        # For naive datetime, use localize to avoid DST issues
        return tz.localize(dt)
    else:
        # For aware datetime, use astimezone
        return dt.astimezone(tz)


def convert_timezone(dt, from_timezone, to_timezone):
    """
    Converts a datetime from one timezone to another.
    
    Args:
        dt (datetime): The datetime to convert.
        from_timezone (str): Source timezone identifier.
        to_timezone (str): Target timezone identifier.
        
    Returns:
        datetime: Datetime in the target timezone.
    """
    if not isinstance(dt, datetime):
        return None
        
    if dt is None:
        return None
        
    # Validate and normalize timezones
    if from_timezone is None or not Timezone.is_valid(from_timezone):
        # If dt has tzinfo, use that, otherwise use default
        if dt.tzinfo is not None:
            from_timezone = str(dt.tzinfo)
        else:
            from_timezone = DEFAULT_TIMEZONE
        
    if to_timezone is None or not Timezone.is_valid(to_timezone):
        to_timezone = DEFAULT_TIMEZONE
        
    from_tz_id = Timezone.get_iana(from_timezone)
    to_tz_id = Timezone.get_iana(to_timezone)
    
    # Localize if needed
    if dt.tzinfo is None:
        dt = localize_datetime(dt, from_tz_id)
    
    # Convert to target timezone
    to_tz = pytz.timezone(to_tz_id)
    return dt.astimezone(to_tz)


def format_datetime(dt, format_str=None):
    """
    Formats a datetime object as a string using standard format.
    
    Args:
        dt (datetime): The datetime to format.
        format_str (str, optional): Format string to use. Defaults to DATETIME_FORMAT.
        
    Returns:
        str: Formatted datetime string, or empty string if input is None.
    """
    if not isinstance(dt, datetime):
        return ""
        
    if dt is None:
        return ""
        
    if format_str is None:
        format_str = DATETIME_FORMAT
        
    return dt.strftime(format_str)


def parse_datetime(datetime_str, format_str=None, timezone_id=None):
    """
    Parses a datetime string into a datetime object.
    
    Args:
        datetime_str (str): The datetime string to parse.
        format_str (str, optional): Format string to use. Defaults to DATETIME_FORMAT.
        timezone_id (str, optional): Timezone to assign to the result.
        
    Returns:
        datetime: Parsed datetime object, or None if parsing fails.
    """
    if not datetime_str or not isinstance(datetime_str, str):
        return None
        
    if format_str is None:
        format_str = DATETIME_FORMAT
        
    try:
        # Try parsing with specified format
        parsed_dt = datetime.strptime(datetime_str, format_str)
    except ValueError:
        try:
            # Fall back to flexible parsing
            parsed_dt = parser.parse(datetime_str)
        except (ValueError, parser.ParserError):
            return None
    
    # Localize if timezone is provided
    if timezone_id is not None and Timezone.is_valid(timezone_id):
        parsed_dt = localize_datetime(parsed_dt, timezone_id)
        
    return parsed_dt


def format_date(dt):
    """
    Formats a date component of a datetime as a string.
    
    Args:
        dt (datetime): The datetime to format.
        
    Returns:
        str: Formatted date string, or empty string if input is None.
    """
    if not isinstance(dt, datetime):
        return ""
        
    if dt is None:
        return ""
        
    return dt.strftime(DATE_FORMAT)


def format_time(dt):
    """
    Formats a time component of a datetime as a string.
    
    Args:
        dt (datetime): The datetime to format.
        
    Returns:
        str: Formatted time string, or empty string if input is None.
    """
    if not isinstance(dt, datetime):
        return ""
        
    if dt is None:
        return ""
        
    return dt.strftime(TIME_FORMAT)


def is_same_day(dt1, dt2, timezone_id=None):
    """
    Checks if two datetimes fall on the same day, optionally in a specific timezone.
    
    Args:
        dt1 (datetime): First datetime.
        dt2 (datetime): Second datetime.
        timezone_id (str, optional): Timezone for comparison.
        
    Returns:
        bool: True if the datetimes are on the same day, False otherwise.
    """
    if not isinstance(dt1, datetime) or not isinstance(dt2, datetime):
        return False
        
    if dt1 is None or dt2 is None:
        return False
        
    # Convert to specific timezone if provided
    if timezone_id is not None:
        if Timezone.is_valid(timezone_id):
            # If specific timezone provided, convert both
            dt1 = convert_timezone(dt1, None, timezone_id)
            dt2 = convert_timezone(dt2, None, timezone_id)
    elif dt1.tzinfo is not None and dt2.tzinfo is not None:
        # If both have timezone info but no specific timezone requested,
        # convert to a common timezone (UTC) for comparison
        dt1 = get_utc_datetime(dt1)
        dt2 = get_utc_datetime(dt2)
        
    # Compare date parts
    return (dt1.year == dt2.year and 
            dt1.month == dt2.month and 
            dt1.day == dt2.day)


def get_current_datetime(timezone_id=None):
    """
    Gets the current datetime, optionally in a specific timezone.
    
    Args:
        timezone_id (str, optional): Timezone for the returned datetime.
            Defaults to DEFAULT_TIMEZONE.
            
    Returns:
        datetime: Current datetime in the specified timezone.
    """
    # Get current UTC time
    now_utc = datetime.now(pytz.UTC)
    
    # Use default timezone if none provided
    if timezone_id is None:
        timezone_id = DEFAULT_TIMEZONE
        
    # Validate and normalize timezone
    if not Timezone.is_valid(timezone_id):
        timezone_id = DEFAULT_TIMEZONE
        
    tz_id = Timezone.get_iana(timezone_id)
    
    # Convert to requested timezone
    return now_utc.astimezone(pytz.timezone(tz_id))