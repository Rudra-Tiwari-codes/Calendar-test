from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from supabase import create_client
from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.logging import get_logger
from ..infra.crypto import decrypt_token
from ..infra.settings import settings
from ..infra.db import session_scope
from ..infra.event_repository import EventRepository
from ..infra.repo import get_user_token_by_discord_id
from ..domain.models import User, Event, Reminder

logger = get_logger().bind(service="calendar_service")


class GoogleCalendarService:
    """Service for managing Google Calendar operations with full database integration."""
    
    def __init__(self, event_repo: Optional[EventRepository] = None, reminder_repo: Optional[Any] = None):
        """Initialize service with optional repositories (will create if not provided)."""
        if not settings.supabase_url:
            raise ValueError("Supabase URL must be configured")
            
        # Use service role key for backend operations
        supabase_key = settings.supabase_service_role_key or settings.supabase_key
        if not supabase_key:
            raise ValueError("Supabase key must be configured")
            
        self.supabase = create_client(settings.supabase_url, supabase_key)
        self.event_repo = event_repo
        self.reminder_repo = reminder_repo
    
    def _build_client(self, token: Dict[str, Any]) -> Any:
        """Build Google Calendar API client from token."""
        try:
            creds = Credentials(
                token=token.get("access_token"),
                refresh_token=token.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/calendar.events",
                ],
            )
            return build("calendar", "v3", credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.error("build_client_failed", error=str(e))
            raise
    
    async def _get_user_token_supabase(self, discord_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user token from Supabase using SQL query."""
        try:
            # Query Supabase for user token
            response = self.supabase.table('users').select('token_ciphertext').eq('discord_id', discord_user_id).execute()
            
            if not response.data:
                logger.warning("user_not_found_in_supabase", discord_user_id=discord_user_id)
                return None
                
            token_ciphertext = response.data[0].get('token_ciphertext')
            if not token_ciphertext:
                logger.warning("user_has_no_token", discord_user_id=discord_user_id)
                return None
            
            # Decrypt token
            from ..infra.crypto import decrypt_text
            token_json = decrypt_text(token_ciphertext)
            return json.loads(token_json)
            
        except Exception as e:
            logger.error("get_user_token_failed", discord_user_id=discord_user_id, error=str(e))
            return None
    
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
            # Get user token using Supabase auth (simplified for reliability)
            token = await self._get_user_token_supabase(discord_user_id)
            if not token:
                raise ValueError("User not found or not connected to Google Calendar")
            
            logger.info("creating_event", user_id=discord_user_id, title=title)
            
            # Build event body for Google Calendar with proper timezone handling
            event_body = {
                "summary": title,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": str(start_time.tzinfo)
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": str(end_time.tzinfo)
                },
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
            
            logger.info("event_created_successfully", 
                       google_event_id=google_event["id"],
                       user_id=discord_user_id)
            
            return {
                "success": True,
                "message": f"✅ Event '{title}' created successfully!",
                "event_id": google_event["id"],  # Direct field for Discord bot
                "event_url": google_event.get("htmlLink"),  # Direct field for Discord bot
                "event": {
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
    
    async def _get_user_with_token(self, discord_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user with valid token using Supabase."""
        try:
            result = self.supabase.table("users").select("*").eq("discord_id", discord_user_id).execute()
            
            if result.data and result.data[0].get("token_ciphertext"):
                return result.data[0]
            return None
        except Exception as e:
            logger.error("get_user_with_token_failed", error=str(e))
            return None
    
    async def _get_valid_token(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get and validate user's Google token."""
        try:
            token_ciphertext = user_data.get("token_ciphertext")
            if not token_ciphertext:
                raise ValueError("No token found for user")
            
            # Decrypt token
            token_data = decrypt_token(token_ciphertext)
            token = json.loads(token_data)
            
            # Validate token has required fields
            if "access_token" not in token:
                raise ValueError("Missing access_token in token")
            
            return token
            
        except Exception as e:
            logger.error("get_valid_token_failed", error=str(e))
            raise ValueError(f"Invalid or expired token: {str(e)}")
