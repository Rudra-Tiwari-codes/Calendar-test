from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import discord
from discord import app_commands

from ..infra.logging import get_logger
from ..infra.settings import settings
from ..infra.date_parsing import parse_natural_range, parse_natural_datetime, extract_event_details
from ..services.calendar_service_simple import GoogleCalendarService
from ..app.oauth import oauth_handler
from ..infra.metrics import events_created_total
from ..infra.rate_limit import check_rate_limit

logger = get_logger().bind(service="discord")


class DiscordClient(discord.Client):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.calendar_service = None

    async def setup_hook(self) -> None:
        await self.tree.sync()
        logger.info("discord_bot_setup_complete")

    async def on_ready(self) -> None:
        logger.info("discord_bot_ready", user=str(self.user))


def build_bot() -> DiscordClient:
    intents = discord.Intents.default()
    client = DiscordClient(intents=intents)

    @client.tree.command(name="ping", description="Ping the bot")
    async def ping_command(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("🏓 Pong! Bot is online and ready.", ephemeral=True)
        logger.info("ping", interaction_id=str(interaction.id))

    @client.tree.command(name="connect", description="Link your Google Calendar account")
    async def connect_command(interaction: discord.Interaction) -> None:
        user_id = str(interaction.user.id)
        
        # Use the new client-side OAuth endpoint
        from events_agent.infra.settings import settings
        url = f"{settings.base_url}/connect/{user_id}"
        
        embed = discord.Embed(
            title="🔗 Connect Google Calendar",
            description="Click the link below to connect your Google Calendar account:",
            color=0x00ff00
        )
        embed.add_field(name="Connection Link", value=f"[Connect Now]({url})", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info("connect_link_sent", interaction_id=str(interaction.id), url=url)

    @client.tree.command(name="addevent", description="Create a calendar event")
    async def addevent_command(
        interaction: discord.Interaction,
        title: str,
        when: str,
        attendees: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        reminder_minutes: Optional[int] = None,
    ) -> None:
        """Create a calendar event with confirmation."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get user's timezone
            async for session in session_scope():
                user_repo = UserRepository(session)
                event_repo = EventRepository(session)
                reminder_repo = ReminderRepository(session)
                calendar_service = GoogleCalendarService(user_repo, event_repo, reminder_repo)
                
                # Get or create user
                user = await user_repo.get_or_create_user(str(interaction.user.id))
                tz = user.tz if user and user.tz else settings.default_tz
                
                # Parse time
                try:
                    start_dt, end_dt = parse_natural_range(when, tz)
                except Exception as e:
                    await interaction.followup.send(
                        f"❌ Sorry, I couldn't parse the time '{when}'. Try formats like:\n"
                        f"• 'tomorrow 3pm'\n"
                        f"• 'next Monday 2-4pm'\n"
                        f"• 'December 25th 10am'",
                        ephemeral=True
                    )
                    return
                
                # Check availability
                availability = await calendar_service.check_availability(
                    str(interaction.user.id), start_dt, end_dt
                )
                
                # Parse attendees
                attendee_list = []
                if attendees:
                    attendee_list = [email.strip() for email in attendees.split(",") if email.strip()]
                
                # Create confirmation embed
                embed = discord.Embed(
                    title="📅 Event Preview",
                    description="Please review the event details below:",
                    color=0x0099ff
                )
                
                embed.add_field(name="📝 Title", value=title, inline=False)
                embed.add_field(
                    name="🕐 Time", 
                    value=f"{start_dt.strftime('%A, %B %d at %I:%M %p')} - {end_dt.strftime('%I:%M %p')}", 
                    inline=False
                )
                embed.add_field(name="🌍 Timezone", value=tz, inline=True)
                
                if location:
                    embed.add_field(name="📍 Location", value=location, inline=True)
                if attendee_list:
                    embed.add_field(name="👥 Attendees", value=", ".join(attendee_list), inline=False)
                if description:
                    embed.add_field(name="📄 Description", value=description[:1000], inline=False)
                if reminder_minutes:
                    embed.add_field(name="⏰ Reminder", value=f"{reminder_minutes} minutes before", inline=True)
                
                # Add availability status
                if not availability.get("available", True):
                    embed.add_field(
                        name="⚠️ Availability", 
                        value="You have conflicts during this time!", 
                        inline=False
                    )
                    embed.color = 0xff9900
                else:
                    embed.add_field(
                        name="✅ Availability", 
                        value="This time slot is available!", 
                        inline=False
                    )
                
                # Create buttons for confirmation
                view = EventConfirmationView(
                    calendar_service=calendar_service,
                    user_id=str(interaction.user.id),
                    title=title,
                    start_time=start_dt,
                    end_time=end_dt,
                    description=description,
                    location=location,
                    attendees=attendee_list,
                    reminder_minutes=reminder_minutes
                )
                
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                break
                
        except Exception as e:
            logger.error("addevent_command_error", error=str(e))
            await interaction.followup.send(
                f"❌ An error occurred while creating the event: {str(e)}", 
                ephemeral=True
            )

    @client.tree.command(name="myevents", description="List your upcoming events")
    async def myevents_command(
        interaction: discord.Interaction,
        limit: int = 5,
    ) -> None:
        """List upcoming events for the user."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async for session in session_scope():
                user_repo = UserRepository(session)
                event_repo = EventRepository(session)
                reminder_repo = ReminderRepository(session)
                calendar_service = GoogleCalendarService(user_repo, event_repo, reminder_repo)
                
                result = await calendar_service.list_events(str(interaction.user.id), limit)
                
                if not result["success"]:
                    await interaction.followup.send(f"❌ {result['message']}", ephemeral=True)
                    return
                
                events = result.get("events", [])
                if not events:
                    await interaction.followup.send("📅 No upcoming events found.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"📅 Your Upcoming Events ({len(events)})",
                    color=0x00ff00
                )
                
                for i, event in enumerate(events, 1):
                    start_time = datetime.fromisoformat(event["start_time"])
                    end_time = datetime.fromisoformat(event["end_time"])
                    
                    event_text = f"**{event['title']}**\n"
                    event_text += f"🕐 {start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}\n"
                    
                    if event.get("location"):
                        event_text += f"📍 {event['location']}\n"
                    if event.get("description"):
                        desc = event["description"][:100] + "..." if len(event["description"]) > 100 else event["description"]
                        event_text += f"📄 {desc}\n"
                    
                    embed.add_field(
                        name=f"{i}. {event['title']}", 
                        value=event_text, 
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                break
                
        except Exception as e:
            logger.error("myevents_command_error", error=str(e))
            await interaction.followup.send(
                f"❌ An error occurred while listing events: {str(e)}", 
                ephemeral=True
            )

    @client.tree.command(name="set-tz", description="Set your timezone")
    async def set_tz_command(interaction: discord.Interaction, timezone: str) -> None:
        """Set user's timezone."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate timezone
            import pytz
            try:
                pytz.timezone(timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                await interaction.followup.send(
                    f"❌ Invalid timezone '{timezone}'. Please use a valid timezone like:\n"
                    f"• 'Australia/Melbourne'\n"
                    f"• 'America/New_York'\n"
                    f"• 'Europe/London'\n"
                    f"• 'Asia/Tokyo'",
                    ephemeral=True
                )
                return
            
            async for session in session_scope():
                user_repo = UserRepository(session)
                user = await user_repo.get_or_create_user(str(interaction.user.id))
                success = await user_repo.update_user_timezone(str(interaction.user.id), timezone)
                
                if success:
                    await interaction.followup.send(
                        f"✅ Timezone set to **{timezone}** successfully!", 
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Failed to update timezone. Please try again.", 
                        ephemeral=True
                    )
                break
                
        except Exception as e:
            logger.error("set_tz_command_error", error=str(e))
            await interaction.followup.send(
                f"❌ An error occurred while setting timezone: {str(e)}", 
                ephemeral=True
            )

    @client.tree.command(name="suggest", description="Suggest optimal meeting times")
    async def suggest_command(
        interaction: discord.Interaction,
        duration_minutes: int = 60,
        days_ahead: int = 7,
    ) -> None:
        """Suggest optimal meeting times."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async for session in session_scope():
                user_repo = UserRepository(session)
                event_repo = EventRepository(session)
                reminder_repo = ReminderRepository(session)
                calendar_service = GoogleCalendarService(user_repo, event_repo, reminder_repo)
                
                result = await calendar_service.suggest_meeting_times(
                    str(interaction.user.id), duration_minutes, days_ahead
                )
                
                if not result["success"]:
                    await interaction.followup.send(f"❌ {result['message']}", ephemeral=True)
                    return
                
                suggestions = result.get("suggestions", [])
                if not suggestions:
                    await interaction.followup.send(
                        f"❌ No available time slots found in the next {days_ahead} days.", 
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title=f"💡 Suggested Meeting Times ({duration_minutes}min)",
                    description=f"Found {len(suggestions)} available slots:",
                    color=0x00ff00
                )
                
                for i, suggestion in enumerate(suggestions[:5], 1):
                    start_time = datetime.fromisoformat(suggestion["start_time"])
                    end_time = datetime.fromisoformat(suggestion["end_time"])
                    
                    embed.add_field(
                        name=f"{i}. {start_time.strftime('%A, %B %d')}",
                        value=f"🕐 {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}",
                        inline=False
                    )
                
                embed.add_field(
                    name="💡 Tip",
                    value="Use `/addevent` with one of these times to create your meeting!",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                break
                
        except Exception as e:
            logger.error("suggest_command_error", error=str(e))
            await interaction.followup.send(
                f"❌ An error occurred while suggesting times: {str(e)}", 
                ephemeral=True
            )

    return client


class EventConfirmationView(discord.ui.View):
    """View for event confirmation with buttons."""
    
    def __init__(
        self,
        calendar_service: GoogleCalendarService,
        user_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str],
        location: Optional[str],
        attendees: list,
        reminder_minutes: Optional[int]
    ):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.calendar_service = calendar_service
        self.user_id = user_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.location = location
        self.attendees = attendees
        self.reminder_minutes = reminder_minutes

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm and create the event."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            result = await self.calendar_service.create_event(
                discord_user_id=self.user_id,
                title=self.title,
                start_time=self.start_time,
                end_time=self.end_time,
                description=self.description,
                location=self.location,
                attendees=self.attendees,
                reminder_minutes=self.reminder_minutes
            )
            
            if result["success"]:
                embed = discord.Embed(
                    title="✅ Event Created Successfully!",
                    description=result["message"],
                    color=0x00ff00
                )
                
                event = result["event"]
                embed.add_field(name="📝 Title", value=event["title"], inline=False)
                embed.add_field(
                    name="🕐 Time", 
                    value=f"{datetime.fromisoformat(event['start_time']).strftime('%A, %B %d at %I:%M %p')} - {datetime.fromisoformat(event['end_time']).strftime('%I:%M %p')}", 
                    inline=False
                )
                
                if event.get("calendar_link"):
                    embed.add_field(
                        name="🔗 Calendar Link", 
                        value=f"[View in Google Calendar]({event['calendar_link']})", 
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                events_created_total.inc()
            else:
                await interaction.followup.send(f"❌ {result['message']}", ephemeral=True)
                
        except Exception as e:
            logger.error("confirm_button_error", error=str(e))
            await interaction.followup.send(
                f"❌ An error occurred while creating the event: {str(e)}", 
                ephemeral=True
            )
        
        # Disable all buttons after confirmation
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel event creation."""
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="❌ Event Creation Cancelled",
            description="The event was not created.",
            color=0xff0000
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label="✏️ Edit", style=discord.ButtonStyle.secondary)
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit event details (placeholder for future implementation)."""
        await interaction.response.send_message(
            "✏️ Edit functionality will be available in a future update. For now, please cancel and create a new event with the correct details.",
            ephemeral=True
        )


async def run_discord_bot(token: str) -> None:
    client = build_bot()
    await client.start(token)