#!/usr/bin/env python3
"""
Enhanced timezone handling utility functions for the Discord bot
"""

import pytz
from datetime import datetime
from events_agent.infra.settings import settings

def parse_datetime_to_local(dt_string: str, user_timezone: str | None = None) -> datetime:
    """
    Parse a datetime string and convert it to the user's local timezone.
    
    Args:
        dt_string: DateTime string from Google Calendar (e.g., "2025-09-26T15:00:00.000Z")
        user_timezone: User's preferred timezone (defaults to Australia/Melbourne)
    
    Returns:
        datetime object in the user's local timezone
    """
    if not user_timezone:
        user_timezone = settings.default_tz
    
    # Parse the datetime string
    dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
    
    # Convert to user's timezone
    local_tz = pytz.timezone(user_timezone)
    dt_local = dt.astimezone(local_tz)
    
    return dt_local

def format_event_time(start_time: str, end_time: str | None = None, user_timezone: str | None = None) -> str:
    """
    Format event time for display in Discord embeds.
    
    Args:
        start_time: Start time string from Google Calendar
        end_time: End time string from Google Calendar (optional)
        user_timezone: User's preferred timezone
    
    Returns:
        Formatted time string for Discord display
    """
    if "T" not in start_time:
        # Date-only event
        return start_time
    
    try:
        start_local = parse_datetime_to_local(start_time, user_timezone)
        
        if end_time and "T" in end_time:
            end_local = parse_datetime_to_local(end_time, user_timezone)
            # Same day event
            if start_local.date() == end_local.date():
                return f"{start_local.strftime('%A, %B %d at %I:%M %p')} - {end_local.strftime('%I:%M %p')}"
            else:
                # Multi-day event
                return f"{start_local.strftime('%A, %B %d at %I:%M %p')} - {end_local.strftime('%A, %B %d at %I:%M %p')}"
        else:
            # Single time
            return start_local.strftime('%A, %B %d at %I:%M %p')
            
    except Exception:
        # Fallback to original strings
        return f"{start_time} - {end_time}" if end_time else start_time