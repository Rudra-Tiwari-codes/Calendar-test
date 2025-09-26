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
    tzinfo = pytz.timezone(tz)
    settings = {
        "RETURN_AS_TIMEZONE_AWARE": True, 
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now(tzinfo),
        "TO_TIMEZONE": tz
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
    tzinfo = pytz.timezone(tz)
    settings = {
        "RETURN_AS_TIMEZONE_AWARE": True, 
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now(tzinfo),
        "TO_TIMEZONE": tz
    }
    
    # Clean up the text like in parse_natural_datetime
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
    
    if " to " in text:
        # Parse range with "to"
        left, right = text.split(" to ", 1)
        start = dateparser.parse(left.strip(), settings=settings)
        end = dateparser.parse(right.strip(), settings=settings)
        
        if not start or not end:
            raise ValueError(f"Could not parse time range: '{text}'")
            
        # If end time is on same day but earlier than start time, assume it's the next day
        if end.date() == start.date() and end.time() < start.time():
            end = end + timedelta(days=1)
    elif "-" in text:
        # Parse range with "-"
        left, right = text.split("-", 1)
        
        start = dateparser.parse(left.strip(), settings=settings)
        end = dateparser.parse(right.strip(), settings=settings)
        
        if not start or not end:
            raise ValueError(f"Could not parse time range: '{text}'")
            
        # If end time is on same day but earlier than start time, assume it's the next day
        if end.date() == start.date() and end.time() < start.time():
            end = end + timedelta(days=1)
    else:
        # Single time - default 1h duration
        start = parsed
        end = parsed + timedelta(hours=1)
    
    # Ensure timezone is correct
    start = start.astimezone(tzinfo)
    end = end.astimezone(tzinfo)
    
    # Handle past times - if the parsed time is in the past and it's a specific time/date,
    # move it to the next occurrence (next day, week, etc.)
    now = datetime.now(tzinfo)
    if start <= now:
        # Check if this looks like a specific date (contains month name or day)
        text_lower = text.lower()
        has_specific_date = any(month in text_lower for month in [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        ])
        
        has_specific_day = any(day in text_lower for day in [
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'
        ])
        
        has_today_tomorrow = any(word in text_lower for word in ['today', 'tomorrow'])
        
        # If it has a specific date/day and is in the past, move to next occurrence
        if has_specific_date or has_specific_day or has_today_tomorrow:
            if has_today_tomorrow and 'today' in text_lower:
                # For "today" with past time, move to tomorrow
                start = start + timedelta(days=1)
                end = end + timedelta(days=1)
            elif has_specific_date and not has_specific_day:
                # Month + date, move to next year if needed
                if start.year == now.year:
                    start = start.replace(year=start.year + 1)
                    end = end.replace(year=end.year + 1)
            elif has_specific_day:
                # Specific day of week, move to next week
                days_ahead = (start.weekday() - now.weekday() + 7) % 7
                if days_ahead == 0:  # Same day
                    days_ahead = 7  # Move to next week
                start = start + timedelta(days=days_ahead)
                end = end + timedelta(days=days_ahead)
    
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


