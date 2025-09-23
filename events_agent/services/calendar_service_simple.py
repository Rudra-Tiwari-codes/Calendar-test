from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from supabase import create_client

from ..infra.logging import get_logger
from ..infra.crypto import decrypt_token
from ..infra.settings import settings

logger = get_logger().bind(service="calendar_service")


class GoogleCalendarService:
    """Simplified Google Calendar service using pure Supabase."""
    
    def __init__(self):
        """Initialize service with Supabase client."""
        if not settings.supabase_url:
            raise ValueError("Supabase URL must be configured")
            
        # Use service role key for backend operations
        supabase_key = settings.supabase_service_role_key or settings.supabase_key
        if not supabase_key:
            raise ValueError("Supabase key must be configured")
            
        self.supabase = create_client(settings.supabase_url, supabase_key)
    
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
    
    async def create_event(
        self,
        discord_user_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
        reminder_minutes: int | None = None,
    ) -> Dict[str, Any]:
        """Create a Google Calendar event."""
        try:
            # Get user and token
            user_data = await self._get_user_with_token(discord_user_id)
            if not user_data:
                raise ValueError("User not found or not connected to Google Calendar")
            
            token = await self._get_valid_token(user_data)
            calendar_client = self._build_client(token)
            
            # Create event body
            event_body = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": user_data.get("tz", "Australia/Melbourne"),
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": user_data.get("tz", "Australia/Melbourne"),
                },
            }
            
            # Add reminder if specified
            if reminder_minutes:
                event_body["reminders"] = {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": reminder_minutes}
                    ],
                }
            
            # Create event in Google Calendar
            google_event = calendar_client.events().insert(
                calendarId="primary", body=event_body
            ).execute()
            
            event_url = google_event.get("htmlLink", "")
            
            logger.info("event_created", 
                       discord_user_id=discord_user_id,
                       event_id=google_event["id"],
                       title=title,
                       has_url=bool(event_url),
                       start_time=start_time.isoformat(),
                       end_time=end_time.isoformat())
            
            return {
                "success": True,
                "event_id": google_event["id"],
                "event_url": event_url,
                "title": title,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }
            
        except Exception as e:
            logger.error("create_event_failed", 
                        discord_user_id=discord_user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    async def list_events(self, discord_user_id: str, limit: int = 5) -> Dict[str, Any]:
        """List upcoming Google Calendar events."""
        try:
            # Get user and token
            user_data = await self._get_user_with_token(discord_user_id)
            if not user_data:
                raise ValueError("User not found or not connected to Google Calendar")
            
            token = await self._get_valid_token(user_data)
            calendar_client = self._build_client(token)
            
            # Get upcoming events
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = calendar_client.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return {
                "success": True,
                "events": [
                    {
                        "id": event["id"],
                        "title": event.get("summary", "No Title"),
                        "start": event["start"].get("dateTime", event["start"].get("date")),
                        "end": event["end"].get("dateTime", event["end"].get("date")),
                        "description": event.get("description", ""),
                        "location": event.get("location", ""),
                        "url": event.get("htmlLink", ""),
                    }
                    for event in events
                ],
                "total": len(events)
            }
            
        except Exception as e:
            logger.error("list_events_failed", 
                        discord_user_id=discord_user_id,
                        error=str(e))
            raise
    
    async def delete_event(self, discord_user_id: str, event_id: str) -> Dict[str, Any]:
        """Delete a specific Google Calendar event."""
        try:
            # Get user and token
            user_data = await self._get_user_with_token(discord_user_id)
            if not user_data:
                raise ValueError("User not found or not connected to Google Calendar")
            
            token = await self._get_valid_token(user_data)
            calendar_client = self._build_client(token)
            
            # Get event details first
            try:
                event = calendar_client.events().get(calendarId='primary', eventId=event_id).execute()
                event_title = event.get('summary', 'Unknown Event')
            except Exception:
                event_title = 'Unknown Event'
            
            # Delete the event
            calendar_client.events().delete(calendarId='primary', eventId=event_id).execute()
            
            logger.info("event_deleted", 
                       discord_user_id=discord_user_id,
                       event_id=event_id,
                       title=event_title)
            
            return {
                "success": True,
                "message": f"Event '{event_title}' has been deleted",
                "event_id": event_id,
                "title": event_title
            }
            
        except Exception as e:
            logger.error("delete_event_failed", 
                        discord_user_id=discord_user_id,
                        event_id=event_id,
                        error=str(e))
            raise
    
    async def update_event(
        self,
        discord_user_id: str,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a specific Google Calendar event."""
        try:
            # Get user and token
            user_data = await self._get_user_with_token(discord_user_id)
            if not user_data:
                raise ValueError("User not found or not connected to Google Calendar")
            
            token = await self._get_valid_token(user_data)
            calendar_client = self._build_client(token)
            
            # Get existing event
            event = calendar_client.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update fields if provided
            if title is not None:
                event['summary'] = title
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            if start_time is not None:
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': user_data.get("tz", "Australia/Melbourne"),
                }
            if end_time is not None:
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': user_data.get("tz", "Australia/Melbourne"),
                }
            
            # Update the event
            updated_event = calendar_client.events().update(
                calendarId='primary', 
                eventId=event_id, 
                body=event
            ).execute()
            
            logger.info("event_updated", 
                       discord_user_id=discord_user_id,
                       event_id=event_id,
                       title=updated_event.get('summary'))
            
            return {
                "success": True,
                "event_id": event_id,
                "title": updated_event.get('summary'),
                "event_url": updated_event.get("htmlLink"),
                "message": "Event updated successfully"
            }
            
        except Exception as e:
            logger.error("update_event_failed", 
                        discord_user_id=discord_user_id,
                        event_id=event_id,
                        error=str(e))
            raise
    
    async def search_events(self, discord_user_id: str, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search for events by title or description."""
        try:
            # Get user and token
            user_data = await self._get_user_with_token(discord_user_id)
            if not user_data:
                raise ValueError("User not found or not connected to Google Calendar")
            
            token = await self._get_valid_token(user_data)
            calendar_client = self._build_client(token)
            
            # Search events
            events_result = calendar_client.events().list(
                calendarId='primary',
                q=query,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return {
                "success": True,
                "query": query,
                "events": [
                    {
                        "id": event["id"],
                        "title": event.get("summary", "No Title"),
                        "start": event["start"].get("dateTime", event["start"].get("date")),
                        "end": event["end"].get("dateTime", event["end"].get("date")),
                        "description": event.get("description", ""),
                        "location": event.get("location", ""),
                        "url": event.get("htmlLink", ""),
                    }
                    for event in events
                ],
                "total": len(events)
            }
            
        except Exception as e:
            logger.error("search_events_failed", 
                        discord_user_id=discord_user_id,
                        query=query,
                        error=str(e))
            raise
    
    async def get_event_details(self, discord_user_id: str, event_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific event."""
        try:
            # Get user and token
            user_data = await self._get_user_with_token(discord_user_id)
            if not user_data:
                raise ValueError("User not found or not connected to Google Calendar")
            
            token = await self._get_valid_token(user_data)
            calendar_client = self._build_client(token)
            
            # Get event details
            event = calendar_client.events().get(calendarId='primary', eventId=event_id).execute()
            
            return {
                "success": True,
                "event": {
                    "id": event["id"],
                    "title": event.get("summary", "No Title"),
                    "start": event["start"].get("dateTime", event["start"].get("date")),
                    "end": event["end"].get("dateTime", event["end"].get("date")),
                    "description": event.get("description", ""),
                    "location": event.get("location", ""),
                    "url": event.get("htmlLink", ""),
                    "created": event.get("created", ""),
                    "updated": event.get("updated", ""),
                    "creator": event.get("creator", {}).get("email", ""),
                    "organizer": event.get("organizer", {}).get("email", ""),
                    "attendees": [
                        {
                            "email": attendee.get("email", ""),
                            "status": attendee.get("responseStatus", "")
                        }
                        for attendee in event.get("attendees", [])
                    ]
                }
            }
            
        except Exception as e:
            logger.error("get_event_details_failed", 
                        discord_user_id=discord_user_id,
                        event_id=event_id,
                        error=str(e))
            raise
    
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