from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import re

import dateparser
import pytz


def parse_natural_datetime(text: str, tz: str = "Australia/Melbourne") -> datetime:
    """
    Parse natural language to datetime object.
    
    Examples:
    - "tomorrow 3pm" -> datetime object
    - "next monday 2pm" -> datetime object
    - "in 2 hours" -> datetime object
    - "december 25th 10am" -> datetime object
    """
    settings = {
        "RETURN_AS_TIMEZONE_AWARE": True, 
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now(pytz.timezone(tz))
    }
    
    # Clean up the text
    text = text.strip().lower()
    
    # Handle common patterns
    text = re.sub(r'\b(\d+)\s*hours?\b', r'\1 hours', text)
    text = re.sub(r'\b(\d+)\s*days?\b', r'\1 days', text)
    text = re.sub(r'\b(\d+)\s*weeks?\b', r'\1 weeks', text)
    
    # Handle "next" patterns
    text = re.sub(r'\bnext\s+(\w+day)\b', r'\1', text)
    text = re.sub(r'\bnext\s+(\w+day)\s+(\d+)\s*(am|pm)\b', r'\1 \2\3', text)
    
    parsed = dateparser.parse(text, settings=settings)
    if not parsed:
        raise ValueError(f"Could not parse time: '{text}'")
    
    # Convert to specified timezone
    tzinfo = pytz.timezone(tz)
    parsed = parsed.astimezone(tzinfo)
    
    return parsed


def parse_natural_range(text: str, tz: str = "Australia/Melbourne") -> Tuple[datetime, datetime]:
    """
    Parse natural language to datetime range (start, end).
    
    Examples:
    - "tomorrow 3pm to 5pm" -> (start_datetime, end_datetime)
    - "next monday 2pm-4pm" -> (start_datetime, end_datetime)
    - "tomorrow 3pm" -> (start_datetime, start_datetime + 1 hour)
    """
    settings = {"RETURN_AS_TIMEZONE_AWARE": True, "PREFER_DATES_FROM": "future"}
    parsed = dateparser.parse(text, settings=settings)
    if not parsed:
        raise ValueError("could_not_parse_time")
    if "to" in text or "-" in text:
        # crude split
        if " to " in text:
            left, right = text.split(" to ", 1)
        else:
            left, right = text.split("-", 1)
        start = dateparser.parse(left, settings=settings)
        end = dateparser.parse(right, settings=settings)
    else:
        # default 1h duration
        start = parsed
        end = parsed + timedelta(hours=1)
    if not start or not end:
        raise ValueError("could_not_parse_time")
    tzinfo = pytz.timezone(tz)
    start = start.astimezone(tzinfo)
    end = end.astimezone(tzinfo)
    return start, end


def extract_event_details(text: str) -> Dict[str, Any]:
    """
    Extract event details from natural language text.
    
    Examples:
    - "Team meeting tomorrow 3pm with @john @jane" -> {
        'title': 'Team meeting',
        'time': 'tomorrow 3pm',
        'attendees': ['@john', '@jane']
      }
    """
    # Extract attendees (mentions)
    attendees = re.findall(r'@\w+', text)
    
    # Remove attendees from text to get clean event description
    clean_text = re.sub(r'@\w+\s*', '', text).strip()
    
    # Try to extract time information
    time_patterns = [
        r'(tomorrow|today|next \w+|in \d+ \w+|this \w+)\s+\d{1,2}(:\d{2})?\s*(am|pm)?',
        r'\d{1,2}(:\d{2})?\s*(am|pm)\s+(tomorrow|today|next \w+)',
        r'(tomorrow|today|next \w+|in \d+ \w+|this \w+)',
    ]
    
    time_match = None
    for pattern in time_patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            time_match = match.group(0)
            break
    
    # Extract title (everything except time and attendees)
    title = clean_text
    if time_match:
        title = clean_text.replace(time_match, '').strip()
    
    return {
        'title': title or 'Event',
        'time': time_match or '',
        'attendees': attendees,
        'description': clean_text
    }


