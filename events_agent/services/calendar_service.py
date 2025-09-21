from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

from ..infra.logging import get_logger
from ..infra.crypto import encrypt_token, decrypt_token
from ..infra.event_repository import EventRepository, UserRepository, ReminderRepository
from ..domain.models import User, Event

logger = get_logger().bind(service="calendar_service")


class GoogleCalendarService:
    """Service for managing Google Calendar operations."""
    
    def __init__(self, user_repo: UserRepository, event_repo: EventRepository, reminder_repo: ReminderRepository):
        self.user_repo = user_repo
        self.event_repo = event_repo
        self.reminder_repo = reminder_repo
    
    def _build_client(self, token: Dict[str, Any]) -> Any:
        """Build Google Calendar API client from token."""
        try:
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
        except Exception as e:
            logger.error("build_client_failed", error=str(e))
            raise
    
    @retry(
        retry=retry_if_exception_type((HttpError, Exception)),
        wait=wait_exponential_jitter(initial=0.5, max=5.0),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def create_event(
        self,
        discord_user_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminder_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a calendar event and store it in the database.
        
        Returns:
            Dict containing event details and confirmation message
        """
        try:
            # Get user and their token
            user = await self._get_user_with_token(discord_user_id)
            if not user:
                raise ValueError("User not found or not connected to Google Calendar")
            
            # Decrypt and validate token
            token = await self._get_valid_token(user)
            
            # Check for duplicate events
            duplicate = await self.event_repo.check_duplicate_event(
                discord_user_id, title, start_time, end_time
            )
            if duplicate:
                logger.warning("duplicate_event_detected", user_id=discord_user_id, title=title)
                return {
                    "success": False,
                    "message": "A similar event already exists at this time. Please choose a different time or modify the event title.",
                    "duplicate_event": {
                        "id": duplicate.id,
                        "title": duplicate.title,
                        "start_time": duplicate.start_time.isoformat(),
                        "end_time": duplicate.end_time.isoformat()
                    }
                }
            
            # Build event body for Google Calendar
            event_body = {
                "summary": title,
                "start": {"dateTime": start_time.isoformat()},
                "end": {"dateTime": end_time.isoformat()},
            }
            
            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location
            if attendees:
                event_body["attendees"] = [{"email": email.strip()} for email in attendees if email.strip()]
            
            # Add reminders
            if reminder_minutes:
                event_body["reminders"] = {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": reminder_minutes}
                    ]
                }
            
            # Create event in Google Calendar
            service = self._build_client(token)
            google_event = await asyncio.to_thread(
                service.events().insert(calendarId="primary", body=event_body).execute
            )
            
            # Store event in database
            db_event = await self.event_repo.create_event(
                user_id=user.id,
                discord_user_id=discord_user_id,
                google_event_id=google_event["id"],
                title=title,
                description=description,
                location=location,
                start_time=start_time,
                end_time=end_time,
                attendees=attendees,
                google_calendar_link=google_event.get("htmlLink")
            )
            
            # Create reminder if specified
            if reminder_minutes:
                reminder_time = start_time - timedelta(minutes=reminder_minutes)
                if reminder_time > datetime.now(timezone.utc):
                    await self.reminder_repo.create_reminder(
                        user_id=user.id,
                        event_id=google_event["id"],
                        channel_id=None,  # Will be set when sending reminder
                        remind_at=reminder_time
                    )
            
            logger.info("event_created_successfully", 
                       event_id=db_event.id, 
                       google_event_id=google_event["id"],
                       user_id=discord_user_id)
            
            return {
                "success": True,
                "message": f"✅ Event '{title}' created successfully!",
                "event": {
                    "id": db_event.id,
                    "google_id": google_event["id"],
                    "title": title,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "location": location,
                    "attendees": attendees or [],
                    "calendar_link": google_event.get("htmlLink"),
                    "description": description
                }
            }
            
        except HttpError as e:
            logger.error("google_calendar_api_error", error=str(e), user_id=discord_user_id)
            return {
                "success": False,
                "message": f"❌ Google Calendar API error: {e.reason if hasattr(e, 'reason') else str(e)}"
            }
        except Exception as e:
            logger.error("create_event_failed", error=str(e), user_id=discord_user_id)
            return {
                "success": False,
                "message": f"❌ Failed to create event: {str(e)}"
            }
    
    async def list_events(self, discord_user_id: str, limit: int = 5) -> Dict[str, Any]:
        """List upcoming events for a user."""
        try:
            # Get user and their token
            user = await self._get_user_with_token(discord_user_id)
            if not user:
                return {
                    "success": False,
                    "message": "User not found or not connected to Google Calendar"
                }
            
            # Get events from database first (faster)
            db_events = await self.event_repo.get_upcoming_events(discord_user_id, limit)
            
            if not db_events:
                return {
                    "success": True,
                    "message": "No upcoming events found.",
                    "events": []
                }
            
            # Format events for display
            events = []
            for event in db_events:
                events.append({
                    "id": event.id,
                    "title": event.title,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "location": event.location,
                    "description": event.description,
                    "calendar_link": event.google_calendar_link
                })
            
            return {
                "success": True,
                "message": f"Found {len(events)} upcoming events:",
                "events": events
            }
            
        except Exception as e:
            logger.error("list_events_failed", error=str(e), user_id=discord_user_id)
            return {
                "success": False,
                "message": f"❌ Failed to list events: {str(e)}"
            }
    
    async def check_availability(
        self,
        discord_user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Check if a user is available during a specific time period."""
        try:
            user = await self._get_user_with_token(discord_user_id)
            if not user:
                return {
                    "success": False,
                    "message": "User not found or not connected to Google Calendar"
                }
            
            token = await self._get_valid_token(user)
            service = self._build_client(token)
            
            # Check free/busy
            time_min = start_time.astimezone(timezone.utc).isoformat()
            time_max = end_time.astimezone(timezone.utc).isoformat()
            
            freebusy_body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": "primary"}]
            }
            
            freebusy_result = await asyncio.to_thread(
                service.freebusy().query(body=freebusy_body).execute
            )
            
            busy_periods = freebusy_result.get("calendars", {}).get("primary", {}).get("busy", [])
            
            if busy_periods:
                conflicts = []
                for period in busy_periods:
                    conflicts.append({
                        "start": period["start"],
                        "end": period["end"]
                    })
                
                return {
                    "success": True,
                    "available": False,
                    "conflicts": conflicts,
                    "message": f"⚠️ You have {len(conflicts)} conflict(s) during this time."
                }
            else:
                return {
                    "success": True,
                    "available": True,
                    "conflicts": [],
                    "message": "✅ This time slot is available!"
                }
                
        except Exception as e:
            logger.error("check_availability_failed", error=str(e), user_id=discord_user_id)
            return {
                "success": False,
                "message": f"❌ Failed to check availability: {str(e)}"
            }
    
    async def suggest_meeting_times(
        self,
        discord_user_id: str,
        duration_minutes: int = 60,
        days_ahead: int = 7,
        preferred_start_hour: int = 9,
        preferred_end_hour: int = 17
    ) -> Dict[str, Any]:
        """Suggest optimal meeting times for a user."""
        try:
            user = await self._get_user_with_token(discord_user_id)
            if not user:
                return {
                    "success": False,
                    "message": "User not found or not connected to Google Calendar"
                }
            
            token = await self._get_valid_token(user)
            service = self._build_client(token)
            
            # Calculate time range
            now = datetime.now(timezone.utc)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=days_ahead)).isoformat()
            
            # Get free/busy data
            freebusy_body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": "primary"}]
            }
            
            freebusy_result = await asyncio.to_thread(
                service.freebusy().query(body=freebusy_body).execute
            )
            
            # Find available slots
            suggestions = self._find_available_slots(
                freebusy_result,
                duration_minutes,
                preferred_start_hour,
                preferred_end_hour
            )
            
            return {
                "success": True,
                "suggestions": suggestions,
                "message": f"Found {len(suggestions)} available time slots."
            }
            
        except Exception as e:
            logger.error("suggest_meeting_times_failed", error=str(e), user_id=discord_user_id)
            return {
                "success": False,
                "message": f"❌ Failed to suggest meeting times: {str(e)}"
            }
    
    def _find_available_slots(
        self,
        freebusy_data: Dict[str, Any],
        duration_minutes: int,
        preferred_start_hour: int,
        preferred_end_hour: int
    ) -> List[Dict[str, Any]]:
        """Find available time slots from free/busy data."""
        suggestions = []
        
        # Get busy periods
        busy_periods = freebusy_data.get("calendars", {}).get("primary", {}).get("busy", [])
        
        # Convert to datetime objects
        busy_times = []
        for period in busy_periods:
            start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
            busy_times.append((start, end))
        
        # Sort busy times
        busy_times.sort(key=lambda x: x[0])
        
        # Find time range
        time_min = datetime.fromisoformat(freebusy_data["timeMin"].replace("Z", "+00:00"))
        time_max = datetime.fromisoformat(freebusy_data["timeMax"].replace("Z", "+00:00"))
        
        # Generate potential slots
        current = time_min
        duration = timedelta(minutes=duration_minutes)
        
        while current + duration <= time_max:
            # Check if within preferred hours
            if preferred_start_hour <= current.hour < preferred_end_hour:
                slot_end = current + duration
                
                # Check for conflicts
                has_conflict = False
                for busy_start, busy_end in busy_times:
                    if current < busy_end and slot_end > busy_start:
                        has_conflict = True
                        break
                
                if not has_conflict:
                    suggestions.append({
                        "start_time": current.isoformat(),
                        "end_time": slot_end.isoformat(),
                        "duration_minutes": duration_minutes
                    })
            
            # Move to next slot (30-minute increments)
            current += timedelta(minutes=30)
        
        return suggestions[:10]  # Return top 10 suggestions
    
    async def _get_user_with_token(self, discord_user_id: str) -> Optional[User]:
        """Get user with valid token."""
        try:
            user = await self.user_repo.get_user_by_discord_id(discord_user_id)
            if user and user.token_ciphertext:
                return user
            return None
        except Exception as e:
            logger.error("get_user_with_token_failed", error=str(e))
            return None
    
    async def _get_valid_token(self, user: User) -> Dict[str, Any]:
        """Get and validate user's Google token."""
        try:
            if not user.token_ciphertext:
                raise ValueError("No token found for user")
            
            # Decrypt token
            token_data = decrypt_token(user.token_ciphertext)
            token = json.loads(token_data)
            
            # Validate token has required fields
            required_fields = ["access_token", "refresh_token", "client_id", "client_secret"]
            for field in required_fields:
                if field not in token:
                    raise ValueError(f"Missing required token field: {field}")
            
            return token
            
        except Exception as e:
            logger.error("get_valid_token_failed", error=str(e))
            raise ValueError(f"Invalid or expired token: {str(e)}")
