from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

import discord

from ..infra.logging import get_logger
from ..infra.event_repository import EventRepository, UserRepository, ReminderRepository
from ..domain.models import Reminder, Event, User
from ..infra.db import session_scope

logger = get_logger().bind(service="reminder")


class ReminderService:
    """Service for managing event reminders and Discord notifications."""
    
    def __init__(self, discord_client: Optional[discord.Client] = None):
        self.discord_client = discord_client
    
    async def process_due_reminders(self) -> None:
        """Process all due reminders and send Discord notifications."""
        try:
            async for session in session_scope():
                reminder_repo = ReminderRepository(session)
                event_repo = EventRepository(session)
                user_repo = UserRepository(session)
                
                # Get all due reminders
                now = datetime.now(timezone.utc)
                due_reminders = await reminder_repo.get_due_reminders(now)
                
                logger.info("processing_reminders", count=len(due_reminders))
                
                for reminder in due_reminders:
                    try:
                        await self._send_reminder_notification(reminder, event_repo, user_repo)
                        await reminder_repo.mark_reminder_sent(reminder.id)
                        
                    except Exception as e:
                        logger.error("reminder_send_failed", 
                                   reminder_id=reminder.id, 
                                   error=str(e))
                        
                        # Increment retry count
                        await reminder_repo.increment_reminder_retries(reminder.id)
                
                break
                
        except Exception as e:
            logger.error("process_due_reminders_failed", error=str(e))
    
    async def _send_reminder_notification(
        self, 
        reminder: Reminder, 
        event_repo: EventRepository, 
        user_repo: UserRepository
    ) -> None:
        """Send a reminder notification to Discord."""
        try:
            if not self.discord_client:
                logger.warning("discord_client_not_available")
                return
            
            # Get user
            from sqlalchemy import select
            result = await user_repo.session.execute(
                select(User).where(User.id == reminder.user_id)
            )
            user_data = result.scalar_one_or_none()
            
            if not user_data:
                logger.warning("user_not_found", user_id=reminder.user_id)
                return
            
            discord_user_id = user_data.discord_id
            
            # Get event details if available
            event_details = None
            if reminder.event_id:
                event = await event_repo.get_event_by_google_id(reminder.event_id)
                if event:
                    event_details = {
                        "title": event.title,
                        "start_time": event.start_time,
                        "end_time": event.end_time,
                        "location": event.location,
                        "description": event.description
                    }
            
            # Create reminder message
            embed = await self._create_reminder_embed(reminder, event_details)
            
            # Send DM to user
            try:
                user_obj = await self.discord_client.fetch_user(int(discord_user_id))
                if user_obj:
                    await user_obj.send(embed=embed)
                    logger.info("reminder_sent_successfully", 
                              reminder_id=reminder.id, 
                              user_id=discord_user_id)
                else:
                    logger.warning("discord_user_not_found", discord_user_id=discord_user_id)
                    
            except discord.Forbidden:
                logger.warning("cannot_send_dm", user_id=discord_user_id)
            except Exception as e:
                logger.error("discord_send_failed", error=str(e))
                
        except Exception as e:
            logger.error("send_reminder_notification_failed", error=str(e))
            raise
    
    async def _create_reminder_embed(
        self, 
        reminder: Reminder, 
        event_details: Optional[Dict[str, Any]]
    ) -> discord.Embed:
        """Create a Discord embed for the reminder."""
        embed = discord.Embed(
            title="⏰ Event Reminder",
            color=0xff9900
        )
        
        if event_details:
            embed.add_field(
                name="📅 Event", 
                value=event_details["title"], 
                inline=False
            )
            
            start_time = event_details["start_time"]
            embed.add_field(
                name="🕐 Time", 
                value=start_time.strftime('%A, %B %d at %I:%M %p'), 
                inline=True
            )
            
            if event_details.get("location"):
                embed.add_field(
                    name="📍 Location", 
                    value=event_details["location"], 
                    inline=True
                )
            
            if event_details.get("description"):
                desc = event_details["description"][:200] + "..." if len(event_details["description"]) > 200 else event_details["description"]
                embed.add_field(
                    name="📄 Description", 
                    value=desc, 
                    inline=False
                )
        else:
            embed.add_field(
                name="📅 Event", 
                value="Event details not available", 
                inline=False
            )
        
        embed.add_field(
            name="⏰ Reminder Time", 
            value=reminder.remind_at.strftime('%A, %B %d at %I:%M %p UTC'), 
            inline=False
        )
        
        embed.set_footer(text="Calendar Agent Reminder")
        embed.timestamp = datetime.now(timezone.utc)
        
        return embed
    
    async def create_event_reminder(
        self,
        user_id: int,
        event_id: str,
        event_start_time: datetime,
        reminder_minutes: int = 15
    ) -> bool:
        """Create a reminder for an event."""
        try:
            async for session in session_scope():
                reminder_repo = ReminderRepository(session)
                
                # Calculate reminder time
                reminder_time = event_start_time - timedelta(minutes=reminder_minutes)
                
                # Only create reminder if it's in the future
                if reminder_time > datetime.now(timezone.utc):
                    await reminder_repo.create_reminder(
                        user_id=user_id,
                        event_id=event_id,
                        channel_id=None,
                        remind_at=reminder_time
                    )
                    
                    logger.info("event_reminder_created", 
                              user_id=user_id, 
                              event_id=event_id, 
                              reminder_time=reminder_time)
                    return True
                else:
                    logger.info("reminder_time_in_past", 
                              user_id=user_id, 
                              event_id=event_id, 
                              reminder_time=reminder_time)
                    return False
                
        except Exception as e:
            logger.error("create_event_reminder_failed", error=str(e))
            return False
    
    async def get_user_reminders(self, discord_user_id: str) -> List[Dict[str, Any]]:
        """Get upcoming reminders for a user."""
        try:
            async for session in session_scope():
                user_repo = UserRepository(session)
                reminder_repo = ReminderRepository(session)
                
                # Get user
                user = await user_repo.get_or_create_user(discord_user_id)
                if not user:
                    return []
                
                # Get upcoming reminders
                now = datetime.now(timezone.utc)
                future_time = now + timedelta(days=7)  # Next 7 days
                
                # This would need a custom query to get reminders in a time range
                # For now, we'll return a placeholder
                return []
                
        except Exception as e:
            logger.error("get_user_reminders_failed", error=str(e))
            return []
    
    async def cancel_reminder(self, reminder_id: int) -> bool:
        """Cancel a specific reminder."""
        try:
            async for session in session_scope():
                reminder_repo = ReminderRepository(session)
                
                # Mark reminder as sent (effectively canceling it)
                success = await reminder_repo.mark_reminder_sent(reminder_id)
                
                if success:
                    logger.info("reminder_cancelled", reminder_id=reminder_id)
                
                return success
                
        except Exception as e:
            logger.error("cancel_reminder_failed", error=str(e))
            return False
