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
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        # Debug logging to see what's being generated
        logger.info("debug_settings", http_host=settings.http_host, http_port=settings.http_port, environment=settings.environment)
        logger.info("debug_base_url", base_url=settings.base_url)
        
        url = f"{settings.base_url}/connect/{user_id}"
        
        embed = discord.Embed(
            title="🔗 Connect Google Calendar",
            description="Click the link below to connect your Google Calendar account securely via Supabase OAuth.",
            color=0x00ff00
        )
        embed.add_field(name="Connection Link", value=f"[Connect Now]({url})", inline=False)
        embed.add_field(name="Note", value="This will open in your browser and use Supabase OAuth for secure authentication.", inline=False)
        embed.add_field(name="Debug Info", value=f"Generated URL: `{url}`", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info("connect_link_sent", interaction_id=str(interaction.id), url=url)

    @client.tree.command(name="status", description="Check your Google Calendar connection status")
    async def status_command(interaction: discord.Interaction) -> None:
        """Check if user has connected their Google Calendar."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_connected = await oauth_handler.is_user_connected(str(interaction.user.id))
            
            if user_connected:
                embed = discord.Embed(
                    title="✅ Google Calendar Connected",
                    description="Your Google Calendar is successfully connected!",
                    color=0x00ff00
                )
                embed.add_field(
                    name="Available Commands", 
                    value="• `/addevent` - Create calendar events\n• `/myevents` - View upcoming events\n• `/deleteevent` - Delete events\n• `/modifyevent` - Modify events\n• `/findevent` - Search events\n• `/eventdetails` - Get event details", 
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Google Calendar Not Connected",
                    description="Your Google Calendar is not connected yet.",
                    color=0xff0000
                )
                embed.add_field(
                    name="To Connect", 
                    value="Use `/connect` to link your Google Calendar account", 
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info("status_check", user_id=str(interaction.user.id), connected=user_connected)
            
        except Exception as e:
            logger.error("status_command_error", error=str(e))
            await interaction.followup.send(
                "❌ Error checking connection status. Please try again.",
                ephemeral=True
            )

    @client.tree.command(name="addevent", description="Create a calendar event")
    async def addevent_command(
        interaction: discord.Interaction,
        title: str,
        when: str,
        location: Optional[str] = None,
        description: Optional[str] = None,
        reminder_minutes: Optional[int] = None,
    ) -> None:
        """Create a calendar event."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is connected first
            user_connected = await oauth_handler.is_user_connected(str(interaction.user.id))
            if not user_connected:
                await interaction.followup.send(
                    "❌ Please connect your Google Calendar first using `/connect`",
                    ephemeral=True
                )
                return
            
            # Create calendar service
            calendar_service = GoogleCalendarService()
            
            # Parse time (use default timezone for now)
            tz = settings.default_tz
            try:
                start_dt, end_dt = parse_natural_range(when, tz)
                
                # Log the parsed time for debugging
                logger.info("time_parsed", 
                           when=when, 
                           start_dt=start_dt.isoformat(), 
                           end_dt=end_dt.isoformat(),
                           user_id=str(interaction.user.id))
                
            except Exception as e:
                logger.error("time_parsing_failed", when=when, error=str(e))
                await interaction.followup.send(
                    f"❌ Sorry, I couldn't parse the time '{when}'. Try formats like:\n"
                    f"• 'tomorrow 3pm'\n"
                    f"• 'next Monday 2-4pm'\n"
                    f"• 'December 25th 10am'\n"
                    f"• 'today 2pm'\n"
                    f"• 'in 2 hours'\n\n"
                    f"Error: {str(e)}",
                    ephemeral=True
                )
                return
            
            # Create the event
            result = await calendar_service.create_event(
                discord_user_id=str(interaction.user.id),
                title=title,
                start_time=start_dt,
                end_time=end_dt,
                description=description or "",
                location=location or "",
                reminder_minutes=reminder_minutes,
            )
            
            # Success response
            embed = discord.Embed(
                title="✅ Event Created Successfully!",
                description=f"**{title}** has been added to your Google Calendar",
                color=0x00ff00
            )
            
            # Show time range
            time_str = f"{start_dt.strftime('%B %d, %Y at %I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
            embed.add_field(name="📅 Date & Time", value=time_str, inline=False)
            
            # Add event ID for future reference
            embed.add_field(name="🆔 Event ID", value=f"`{result.get('event_id', 'unknown')}`", inline=False)
            
            if location:
                embed.add_field(name="📍 Location", value=location, inline=False)
            if description:
                embed.add_field(name="📝 Description", value=description, inline=False)
            if reminder_minutes:
                embed.add_field(name="⏰ Reminder", value=f"{reminder_minutes} minutes before", inline=False)
                
            # Add Google Calendar link if available
            event_url = result.get("event_url")
            if event_url:
                embed.add_field(name="🔗 View in Google Calendar", value=f"[Open Event]({event_url})", inline=False)
            else:
                embed.add_field(name="📝 Note", value="Event created successfully! Check your Google Calendar app.", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            events_created_total.inc()
            
        except Exception as e:
            logger.error("addevent_command_error", error=str(e))
            await interaction.followup.send(
                f"❌ Failed to create event: {str(e)}",
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
            # Check if user is connected first
            user_connected = await oauth_handler.is_user_connected(str(interaction.user.id))
            if not user_connected:
                await interaction.followup.send(
                    "❌ Please connect your Google Calendar first using `/connect`",
                    ephemeral=True
                )
                return
            
            # Create calendar service and get events
            calendar_service = GoogleCalendarService()
            result = await calendar_service.list_events(str(interaction.user.id), limit)
            
            events = result.get("events", [])
            
            if not events:
                embed = discord.Embed(
                    title="📅 No Upcoming Events",
                    description="You don't have any upcoming events in your calendar.",
                    color=0x888888
                )
            else:
                embed = discord.Embed(
                    title=f"📅 Your Upcoming Events ({len(events)})",
                    description="Here are your next few events:",
                    color=0x0099ff
                )
                
                for i, event in enumerate(events[:limit], 1):
                    start_time = event.get("start", "")
                    if "T" in start_time:  # datetime format
                        try:
                            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                            time_str = dt.strftime("%b %d, %I:%M %p")
                        except:
                            time_str = start_time
                    else:  # date only format
                        time_str = start_time
                    
                    event_text = f"**{event.get('title', 'No Title')}**\n"
                    event_text += f"🕐 {time_str}\n"
                    if event.get('location'):
                        event_text += f"📍 {event['location']}\n"
                    
                    embed.add_field(
                        name=f"Event {i}",
                        value=event_text,
                        inline=True
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error("myevents_command_error", error=str(e))
            await interaction.followup.send(
                f"❌ Failed to retrieve events: {str(e)}",
                ephemeral=True
            )

    @client.tree.command(name="deleteevent", description="Delete a calendar event")
    async def deleteevent_command(
        interaction: discord.Interaction,
        event_id: str,
    ) -> None:
        """Delete a specific calendar event."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is connected first
            user_connected = await oauth_handler.is_user_connected(str(interaction.user.id))
            if not user_connected:
                await interaction.followup.send(
                    "❌ Please connect your Google Calendar first using `/connect`",
                    ephemeral=True
                )
                return
            
            # Create calendar service and delete event
            calendar_service = GoogleCalendarService()
            result = await calendar_service.delete_event(str(interaction.user.id), event_id)
            
            # Success response
            embed = discord.Embed(
                title="🗑️ Event Deleted",
                description=f"**{result.get('title', 'Event')}** has been removed from your calendar",
                color=0xff6b6b
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error("deleteevent_command_error", error=str(e))
            if "not found" in str(e).lower():
                await interaction.followup.send(
                    "❌ Event not found. Use `/myevents` to see your events and their IDs.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Failed to delete event: {str(e)}",
                    ephemeral=True
                )

    @client.tree.command(name="findevent", description="Search for events by title or description")
    async def findevent_command(
        interaction: discord.Interaction,
        query: str,
        limit: int = 5,
    ) -> None:
        """Search for events matching a query."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is connected first
            user_connected = await oauth_handler.is_user_connected(str(interaction.user.id))
            if not user_connected:
                await interaction.followup.send(
                    "❌ Please connect your Google Calendar first using `/connect`",
                    ephemeral=True
                )
                return
            
            # Create calendar service and search
            calendar_service = GoogleCalendarService()
            result = await calendar_service.search_events(str(interaction.user.id), query, limit)
            
            events = result.get("events", [])
            
            if not events:
                embed = discord.Embed(
                    title="🔍 No Results Found",
                    description=f"No events found matching '{query}'",
                    color=0x888888
                )
            else:
                embed = discord.Embed(
                    title=f"🔍 Search Results for '{query}' ({len(events)})",
                    description="Here are the matching events:",
                    color=0x0099ff
                )
                
                for i, event in enumerate(events[:limit], 1):
                    start_time = event.get("start", "")
                    if "T" in start_time:  # datetime format
                        try:
                            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                            time_str = dt.strftime("%b %d, %I:%M %p")
                        except:
                            time_str = start_time
                    else:  # date only format
                        time_str = start_time
                    
                    event_text = f"**{event.get('title', 'No Title')}**\n"
                    event_text += f"🕐 {time_str}\n"
                    event_text += f"🆔 `{event['id']}`\n"
                    if event.get('location'):
                        event_text += f"📍 {event['location']}\n"
                    
                    embed.add_field(
                        name=f"Result {i}",
                        value=event_text,
                        inline=True
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error("findevent_command_error", error=str(e))
            await interaction.followup.send(
                f"❌ Failed to search events: {str(e)}",
                ephemeral=True
            )

    @client.tree.command(name="eventdetails", description="Get detailed information about an event")
    async def eventdetails_command(
        interaction: discord.Interaction,
        event_id: str,
    ) -> None:
        """Get detailed information about a specific event."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is connected first
            user_connected = await oauth_handler.is_user_connected(str(interaction.user.id))
            if not user_connected:
                await interaction.followup.send(
                    "❌ Please connect your Google Calendar first using `/connect`",
                    ephemeral=True
                )
                return
            
            # Create calendar service and get details
            calendar_service = GoogleCalendarService()
            result = await calendar_service.get_event_details(str(interaction.user.id), event_id)
            
            event = result.get("event", {})
            
            # Create detailed embed
            embed = discord.Embed(
                title=f"📅 {event.get('title', 'No Title')}",
                description="Event Details",
                color=0x0099ff
            )
            
            # Add time information
            start_time = event.get("start", "")
            end_time = event.get("end", "")
            if "T" in start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                    time_str = f"{start_dt.strftime('%A, %B %d at %I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
                except:
                    time_str = f"{start_time} - {end_time}"
            else:
                time_str = f"{start_time} - {end_time}"
            
            embed.add_field(name="🕐 Time", value=time_str, inline=False)
            embed.add_field(name="🆔 Event ID", value=f"`{event_id}`", inline=False)
            
            if event.get('location'):
                embed.add_field(name="📍 Location", value=event['location'], inline=False)
            
            if event.get('description'):
                description = event['description'][:1000]  # Limit length
                embed.add_field(name="📝 Description", value=description, inline=False)
            
            if event.get('creator'):
                embed.add_field(name="👤 Creator", value=event['creator'], inline=True)
            
            if event.get('attendees'):
                attendees_text = "\n".join([
                    f"• {att['email']} ({att['status']})" 
                    for att in event['attendees'][:5]  # Limit to 5
                ])
                embed.add_field(name="👥 Attendees", value=attendees_text, inline=False)
            
            if event.get('url'):
                embed.add_field(name="🔗 Google Calendar", value=f"[View Event]({event['url']})", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error("eventdetails_command_error", error=str(e))
            if "not found" in str(e).lower():
                await interaction.followup.send(
                    "❌ Event not found. Check the event ID and try again.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Failed to get event details: {str(e)}",
                    ephemeral=True
                )

    @client.tree.command(name="modifyevent", description="Modify an existing calendar event")
    async def modifyevent_command(
        interaction: discord.Interaction,
        event_id: str,
        new_title: Optional[str] = None,
        new_time: Optional[str] = None,
        new_location: Optional[str] = None,
        new_description: Optional[str] = None,
    ) -> None:
        """Modify an existing calendar event."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is connected first
            user_connected = await oauth_handler.is_user_connected(str(interaction.user.id))
            if not user_connected:
                await interaction.followup.send(
                    "❌ Please connect your Google Calendar first using `/connect`",
                    ephemeral=True
                )
                return
            
            # Parse new time if provided
            start_dt = None
            end_dt = None
            if new_time:
                try:
                    tz = settings.default_tz
                    start_dt, end_dt = parse_natural_range(new_time, tz)
                except Exception as e:
                    await interaction.followup.send(
                        f"❌ Sorry, I couldn't parse the time '{new_time}'. Try formats like:\n"
                        f"• 'tomorrow 3pm'\n"
                        f"• 'next Monday 2-4pm'\n"
                        f"• 'December 25th 10am'",
                        ephemeral=True
                    )
                    return
            
            # Create calendar service and update event
            calendar_service = GoogleCalendarService()
            result = await calendar_service.update_event(
                discord_user_id=str(interaction.user.id),
                event_id=event_id,
                title=new_title,
                start_time=start_dt,
                end_time=end_dt,
                description=new_description,
                location=new_location,
            )
            
            # Success response
            embed = discord.Embed(
                title="✅ Event Updated",
                description=f"**{result.get('title', 'Event')}** has been modified",
                color=0x00ff00
            )
            
            changes = []
            if new_title:
                changes.append(f"📝 Title: {new_title}")
            if new_time:
                changes.append(f"🕐 Time: {new_time}")
            if new_location:
                changes.append(f"📍 Location: {new_location}")
            if new_description:
                changes.append(f"📄 Description: {new_description[:100]}...")
            
            if changes:
                embed.add_field(name="Changes Made", value="\n".join(changes), inline=False)
            
            if result.get("event_url"):
                embed.add_field(name="🔗 View in Google Calendar", value=f"[Open Event]({result['event_url']})", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error("modifyevent_command_error", error=str(e))
            if "not found" in str(e).lower():
                await interaction.followup.send(
                    "❌ Event not found. Use `/myevents` or `/findevent` to find the correct event ID.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Failed to modify event: {str(e)}",
                    ephemeral=True
                )

    return client


# Keep the original reference for backwards compatibility
def get_client() -> DiscordClient:
    """Get the Discord client instance."""
    return build_bot()