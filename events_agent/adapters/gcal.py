from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type


def _build_client(token: Dict[str, Any]):
    creds = Credentials(
        token=token.get("access_token"),
        refresh_token=token.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=token.get("client_id"),
        client_secret=token.get("client_secret"),
        scopes=[
            "openid",
            "email",
            "https://www.googleapis.com/auth/calendar",
        ],
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential_jitter(initial=0.5, max=5.0),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _freebusy_sync(token: Dict[str, Any], time_min: str, time_max: str, calendar_id: str = "primary") -> Dict[str, Any]:
    service = _build_client(token)
    body = {"timeMin": time_min, "timeMax": time_max, "items": [{"id": calendar_id}]}
    return service.freebusy().query(body=body).execute()


async def get_freebusy(token: Dict[str, Any], time_min: str, time_max: str, calendar_id: str = "primary") -> Dict[str, Any]:
    return await asyncio.to_thread(_freebusy_sync, token, time_min, time_max, calendar_id)


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential_jitter(initial=0.5, max=5.0),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _create_event_sync(token: Dict[str, Any], body: Dict[str, Any], calendar_id: str = "primary") -> Dict[str, Any]:
    service = _build_client(token)
    return service.events().insert(calendarId=calendar_id, body=body).execute()


async def create_event(token: Dict[str, Any], body: Dict[str, Any], calendar_id: str = "primary") -> Dict[str, Any]:
    return await asyncio.to_thread(_create_event_sync, token, body, calendar_id)


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential_jitter(initial=0.5, max=5.0),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _list_events_sync(token: Dict[str, Any], time_min: Optional[str] = None, max_results: int = 5, calendar_id: str = "primary") -> Dict[str, Any]:
    service = _build_client(token)
    kwargs: Dict[str, Any] = {"calendarId": calendar_id, "maxResults": max_results, "singleEvents": True, "orderBy": "startTime"}
    if time_min:
        kwargs["timeMin"] = time_min
    return service.events().list(**kwargs).execute()


async def list_events(token: Dict[str, Any], time_min: Optional[str] = None, max_results: int = 5, calendar_id: str = "primary") -> Dict[str, Any]:
    return await asyncio.to_thread(_list_events_sync, token, time_min, max_results, calendar_id)


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential_jitter(initial=0.5, max=5.0),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _get_multiple_freebusy_sync(tokens: List[Dict[str, Any]], time_min: str, time_max: str) -> Dict[str, Any]:
    """Get free/busy information for multiple users simultaneously."""
    service = _build_client(tokens[0])  # Use first token for API calls
    
    # Build request body with all calendars
    items = []
    for token in tokens:
        # Get user's email/calendar ID from token
        calendar_id = token.get("calendar_id", "primary")
        items.append({"id": calendar_id})
    
    body = {"timeMin": time_min, "timeMax": time_max, "items": items}
    return service.freebusy().query(body=body).execute()


async def get_multiple_freebusy(tokens: List[Dict[str, Any]], time_min: str, time_max: str) -> Dict[str, Any]:
    """Get free/busy information for multiple users."""
    return await asyncio.to_thread(_get_multiple_freebusy_sync, tokens, time_min, time_max)


def find_optimal_time_slots(
    freebusy_data: Dict[str, Any], 
    duration_minutes: int = 60,
    preferred_start_hour: int = 9,
    preferred_end_hour: int = 17,
    buffer_minutes: int = 15
) -> List[Tuple[datetime, datetime]]:
    """
    Find optimal time slots based on free/busy data.
    
    Args:
        freebusy_data: Free/busy data from Google Calendar API
        duration_minutes: Duration of the meeting in minutes
        preferred_start_hour: Preferred start hour (24-hour format)
        preferred_end_hour: Preferred end hour (24-hour format)
        buffer_minutes: Buffer time between meetings
    
    Returns:
        List of (start_time, end_time) tuples for available slots
    """
    available_slots = []
    
    # Parse free/busy data
    calendars = freebusy_data.get("calendars", {})
    
    # Get busy periods from all calendars
    all_busy_periods = []
    for calendar_id, calendar_data in calendars.items():
        busy_periods = calendar_data.get("busy", [])
        for period in busy_periods:
            start_time = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
            all_busy_periods.append((start_time, end_time))
    
    # Sort busy periods by start time
    all_busy_periods.sort(key=lambda x: x[0])
    
    # Find time range to search
    time_min = datetime.fromisoformat(freebusy_data["timeMin"].replace("Z", "+00:00"))
    time_max = datetime.fromisoformat(freebusy_data["timeMax"].replace("Z", "+00:00"))
    
    # Generate potential time slots
    current_time = time_min
    slot_duration = timedelta(minutes=duration_minutes)
    buffer_duration = timedelta(minutes=buffer_minutes)
    
    while current_time + slot_duration <= time_max:
        # Check if this time slot is within preferred hours
        if preferred_start_hour <= current_time.hour < preferred_end_hour:
            slot_end = current_time + slot_duration
            
            # Check for conflicts with busy periods
            has_conflict = False
            for busy_start, busy_end in all_busy_periods:
                # Check if there's any overlap (with buffer)
                if (current_time - buffer_duration < busy_end and 
                    slot_end + buffer_duration > busy_start):
                    has_conflict = True
                    break
            
            if not has_conflict:
                available_slots.append((current_time, slot_end))
        
        # Move to next potential slot (30-minute increments)
        current_time += timedelta(minutes=30)
    
    return available_slots[:10]  # Return top 10 slots


async def suggest_meeting_times(
    organizer_token: Dict[str, Any],
    attendee_tokens: List[Dict[str, Any]],
    duration_minutes: int = 60,
    days_ahead: int = 7,
    preferred_start_hour: int = 9,
    preferred_end_hour: int = 17
) -> List[Dict[str, Any]]:
    """
    Suggest optimal meeting times for multiple attendees.
    
    Args:
        organizer_token: Token for the meeting organizer
        attendee_tokens: List of tokens for attendees
        duration_minutes: Meeting duration in minutes
        days_ahead: How many days ahead to search
        preferred_start_hour: Preferred start hour (24-hour format)
        preferred_end_hour: Preferred end hour (24-hour format)
    
    Returns:
        List of suggested time slots with availability info
    """
    # Calculate time range
    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"
    
    # Get free/busy data for all attendees
    all_tokens = [organizer_token] + attendee_tokens
    freebusy_data = await get_multiple_freebusy(all_tokens, time_min, time_max)
    
    # Find optimal time slots
    slots = find_optimal_time_slots(
        freebusy_data, 
        duration_minutes, 
        preferred_start_hour, 
        preferred_end_hour
    )
    
    # Format suggestions
    suggestions = []
    for start_time, end_time in slots:
        suggestions.append({
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration_minutes,
            "available_for_all": True,  # Since we filtered for conflicts
            "timezone": "UTC"  # Could be enhanced to use user's timezone
        })
    
    return suggestions


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential_jitter(initial=0.5, max=5.0),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _create_recurring_event_sync(token: Dict[str, Any], body: Dict[str, Any], calendar_id: str = "primary") -> Dict[str, Any]:
    """Create a recurring event with RRULE."""
    service = _build_client(token)
    return service.events().insert(calendarId=calendar_id, body=body).execute()


async def create_recurring_event(token: Dict[str, Any], body: Dict[str, Any], calendar_id: str = "primary") -> Dict[str, Any]:
    """Create a recurring event."""
    return await asyncio.to_thread(_create_recurring_event_sync, token, body, calendar_id)


def build_rrule(frequency: str, interval: int = 1, count: Optional[int] = None, until: Optional[str] = None, byday: Optional[List[str]] = None) -> str:
    """
    Build an RRULE string for recurring events.
    
    Args:
        frequency: FREQ value (DAILY, WEEKLY, MONTHLY, YEARLY)
        interval: INTERVAL value (default 1)
        count: COUNT value (number of occurrences)
        until: UNTIL value (end date)
        byday: BYDAY value (list of days like ['MO', 'WE', 'FR'])
    
    Returns:
        RRULE string
    """
    rrule_parts = [f"FREQ={frequency}", f"INTERVAL={interval}"]
    
    if count:
        rrule_parts.append(f"COUNT={count}")
    elif until:
        rrule_parts.append(f"UNTIL={until}")
    
    if byday:
        rrule_parts.append(f"BYDAY={','.join(byday)}")
    
    return ";".join(rrule_parts)


