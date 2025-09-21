from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import Event, User, Reminder, EventTemplate
from .logging import get_logger

logger = get_logger().bind(service="event_repository")


class EventRepository:
    """Repository for managing calendar events in the database."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_event(
        self,
        user_id: int,
        discord_user_id: str,
        google_event_id: str,
        title: str,
        description: Optional[str],
        location: Optional[str],
        start_time: datetime,
        end_time: datetime,
        attendees: Optional[List[str]] = None,
        google_calendar_link: Optional[str] = None
    ) -> Event:
        """Create a new event in the database."""
        try:
            attendees_json = json.dumps(attendees) if attendees else None
            
            event = Event(
                user_id=user_id,
                discord_user_id=discord_user_id,
                google_event_id=google_event_id,
                title=title,
                description=description,
                location=location,
                start_time=start_time,
                end_time=end_time,
                attendees=attendees_json,
                google_calendar_link=google_calendar_link,
                reminder_sent=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.session.add(event)
            await self.session.commit()
            await self.session.refresh(event)
            
            logger.info("event_created", event_id=event.id, google_event_id=google_event_id)
            return event
            
        except Exception as e:
            await self.session.rollback()
            logger.error("event_creation_failed", error=str(e))
            raise
    
    async def get_event_by_google_id(self, google_event_id: str) -> Optional[Event]:
        """Get an event by its Google Calendar ID."""
        try:
            result = await self.session.execute(
                select(Event).where(Event.google_event_id == google_event_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("get_event_by_google_id_failed", error=str(e))
            return None
    
    async def get_events_by_user(self, discord_user_id: str, limit: int = 10) -> List[Event]:
        """Get events for a specific user."""
        try:
            result = await self.session.execute(
                select(Event)
                .where(Event.discord_user_id == discord_user_id)
                .order_by(Event.start_time.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("get_events_by_user_failed", error=str(e))
            return []
    
    async def get_upcoming_events(self, discord_user_id: str, limit: int = 5) -> List[Event]:
        """Get upcoming events for a user."""
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                select(Event)
                .where(
                    and_(
                        Event.discord_user_id == discord_user_id,
                        Event.start_time > now
                    )
                )
                .order_by(Event.start_time.asc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("get_upcoming_events_failed", error=str(e))
            return []
    
    async def list_events_for_user(self, user_id: int, limit: int = 10) -> List[Event]:
        """List events for a user by user ID."""
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                select(Event)
                .where(
                    and_(
                        Event.user_id == user_id,
                        Event.start_time > now
                    )
                )
                .order_by(Event.start_time.asc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("list_events_for_user_failed", error=str(e))
            return []
    
    async def check_duplicate_event(
        self,
        discord_user_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        tolerance_minutes: int = 15
    ) -> Optional[Event]:
        """Check if a similar event already exists within a time tolerance."""
        try:
            from datetime import timedelta
            tolerance = timedelta(minutes=tolerance_minutes)
            
            result = await self.session.execute(
                select(Event).where(
                    and_(
                        Event.discord_user_id == discord_user_id,
                        Event.title.ilike(f"%{title}%"),
                        Event.start_time >= start_time - tolerance,
                        Event.start_time <= start_time + tolerance
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("check_duplicate_event_failed", error=str(e))
            return None
    
    async def update_event_reminder_sent(self, event_id: int) -> bool:
        """Mark an event's reminder as sent."""
        try:
            await self.session.execute(
                update(Event)
                .where(Event.id == event_id)
                .values(reminder_sent=True, updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error("update_event_reminder_sent_failed", error=str(e))
            return False
    
    async def delete_event(self, google_event_id: str) -> bool:
        """Delete an event from the database."""
        try:
            await self.session.execute(
                delete(Event).where(Event.google_event_id == google_event_id)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error("delete_event_failed", error=str(e))
            return False


class UserRepository:
    """Repository for managing users in the database."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_discord_id(self, discord_id: str) -> Optional[User]:
        """Get a user by their Discord ID."""
        try:
            result = await self.session.execute(
                select(User).where(User.discord_id == discord_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("get_user_by_discord_id_failed", error=str(e))
            return None
    
    async def create_user(self, discord_id: str, username: str, email: Optional[str] = None) -> User:
        """Create a new user."""
        try:
            user = User(
                discord_id=discord_id,
                email=email,
                tz=None,
                google_sub=None,
                token_ciphertext=None
            )
            
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            
            logger.info("user_created", user_id=user.id, discord_id=discord_id)
            return user
            
        except Exception as e:
            await self.session.rollback()
            logger.error("create_user_failed", error=str(e))
            raise
    
    async def get_or_create_user(self, discord_id: str, email: Optional[str] = None) -> User:
        """Get an existing user or create a new one."""
        try:
            # Try to get existing user
            user = await self.get_user_by_discord_id(discord_id)
            
            if user:
                return user
            
            # Create new user
            user = User(
                discord_id=discord_id,
                email=email,
                tz=None,
                google_sub=None,
                token_ciphertext=None
            )
            
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            
            logger.info("user_created", user_id=user.id, discord_id=discord_id)
            return user
            
        except Exception as e:
            await self.session.rollback()
            logger.error("get_or_create_user_failed", error=str(e))
            raise
    
    async def update_user_timezone(self, discord_id: str, timezone: str) -> bool:
        """Update a user's timezone."""
        try:
            await self.session.execute(
                update(User)
                .where(User.discord_id == discord_id)
                .values(tz=timezone)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error("update_user_timezone_failed", error=str(e))
            return False
    
    async def update_user_token(self, discord_id: str, token_ciphertext: str, google_sub: str) -> bool:
        """Update a user's encrypted Google token."""
        try:
            await self.session.execute(
                update(User)
                .where(User.discord_id == discord_id)
                .values(token_ciphertext=token_ciphertext, google_sub=google_sub)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error("update_user_token_failed", error=str(e))
            return False
    
    async def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user fields."""
        try:
            await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(**kwargs)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error("update_user_failed", error=str(e))
            return False


class ReminderRepository:
    """Repository for managing reminders in the database."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_reminder(
        self,
        user_id: int,
        event_id: Optional[str],
        channel_id: Optional[str],
        remind_at: datetime,
        retries: int = 0
    ) -> Reminder:
        """Create a new reminder."""
        try:
            reminder = Reminder(
                user_id=user_id,
                event_id=event_id,
                channel_id=channel_id,
                remind_at=remind_at,
                sent=False,
                retries=retries
            )
            
            self.session.add(reminder)
            await self.session.commit()
            await self.session.refresh(reminder)
            
            logger.info("reminder_created", reminder_id=reminder.id, remind_at=remind_at)
            return reminder
            
        except Exception as e:
            await self.session.rollback()
            logger.error("reminder_creation_failed", error=str(e))
            raise
    
    async def get_due_reminders(self, current_time: datetime) -> List[Reminder]:
        """Get reminders that are due to be sent."""
        try:
            result = await self.session.execute(
                select(Reminder).where(
                    and_(
                        Reminder.sent == False,
                        Reminder.remind_at <= current_time
                    )
                )
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("get_due_reminders_failed", error=str(e))
            return []
    
    async def mark_reminder_sent(self, reminder_id: int) -> bool:
        """Mark a reminder as sent."""
        try:
            await self.session.execute(
                update(Reminder)
                .where(Reminder.id == reminder_id)
                .values(sent=True)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error("mark_reminder_sent_failed", error=str(e))
            return False
    
    async def increment_reminder_retries(self, reminder_id: int) -> bool:
        """Increment the retry count for a reminder."""
        try:
            await self.session.execute(
                update(Reminder)
                .where(Reminder.id == reminder_id)
                .values(retries=Reminder.retries + 1)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error("increment_reminder_retries_failed", error=str(e))
            return False
