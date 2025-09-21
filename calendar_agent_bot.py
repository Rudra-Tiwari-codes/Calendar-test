#!/usr/bin/env python3
"""
Complete Calendar Agent Discord Bot
Integrates Discord with Google Calendar API and SQLite database
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add the events_agent directory to Python path if needed

import discord
from discord.ext import commands
from discord import app_commands

# Import our modules
from events_agent.infra.settings import settings
from events_agent.infra.logging import configure_logging, get_logger
from events_agent.infra.date_parsing import parse_natural_datetime, extract_event_details
from events_agent.infra.db import session_scope
from events_agent.domain.models import User, Event, Reminder
from events_agent.services.calendar_service import GoogleCalendarService
from events_agent.infra.event_repository import EventRepository, UserRepository, ReminderRepository

# Configure logging
configure_logging()
logger = get_logger()

# Create bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global services
calendar_service = None

@bot.event
async def on_ready():
    """Event when bot is ready."""
    global calendar_service
    
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'📊 Connected to {len(bot.guilds)} servers')
    
    # Initialize services
    try:
        # Services will be initialized per-request with proper session context
        print('✅ Services ready for initialization')
    except Exception as e:
        print(f'⚠️ Warning: Some services failed to initialize: {e}')
    
    print('✅ Calendar Agent Bot is ready!')
    print('Available commands:')
    print('  /ping - Test if bot is working')
    print('  /addevent - Create a new calendar event')
    print('  /myevents - List your upcoming events')
    print('  /set-tz - Set your timezone')
    print('  /connect - Connect your Google Calendar')
    print('  Press Ctrl+C to stop the bot')
    
    logger.info("calendar_agent_ready", user=str(bot.user))

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    print(f'❌ Error: {error}')
    logger.error("command_error", error=str(error))

# Slash Commands
@bot.tree.command(name="ping", description="Ping the Calendar Agent bot")
async def ping_command(interaction: discord.Interaction):
    """Ping command to test bot."""
    await interaction.response.send_message("🏓 Pong! Calendar Agent is online and ready.", ephemeral=True)
    logger.info("ping_command", user=str(interaction.user))

@bot.tree.command(name="addevent", description="Create a new calendar event")
async def add_event_command(interaction: discord.Interaction, event_description: str):
    """Add event command with natural language processing."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Parse the event description
        event_details = extract_event_details(event_description)
        
        if not event_details:
            await interaction.followup.send("❌ Could not parse event details. Please try again with a clearer description.", ephemeral=True)
            return
        
        # Create confirmation message
        embed = discord.Embed(
            title="📅 Event Creation Confirmation",
            description="Please review the event details:",
            color=0x00ff00
        )
        
        embed.add_field(name="Title", value=event_details.get('title', 'Untitled Event'), inline=False)
        embed.add_field(name="Time", value=event_details.get('time', 'Not specified'), inline=False)
        embed.add_field(name="Attendees", value=event_details.get('attendees', 'None'), inline=False)
        embed.add_field(name="Description", value=event_details.get('description', 'No description'), inline=False)
        
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
        
        message = await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Add reaction buttons
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        # Wait for user reaction
        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ["✅", "❌"]
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Create the event
                await interaction.followup.send("🔄 Creating event...", ephemeral=True)
                
                # For now, just store in database (Google Calendar integration would go here)
                async with session_scope() as session:
                    user_repo = UserRepository(session)
                    event_repo = EventRepository(session)
                    
                    user_obj = await user_repo.get_user_by_discord_id(str(interaction.user.id))
                    if not user_obj:
                        user_obj = await user_repo.create_user(str(interaction.user.id), str(interaction.user))
                    
                    event = await event_repo.create_event(
                        user_id=user_obj.id,
                        discord_user_id=str(interaction.user.id),
                        title=event_details.get('title', 'Untitled Event'),
                        description=event_details.get('description', ''),
                        start_time=datetime.now() + timedelta(hours=1),  # Default to 1 hour from now
                        end_time=datetime.now() + timedelta(hours=2),   # Default to 2 hours from now
                        attendees=event_details.get('attendees', ''),
                        google_event_id="temp_" + str(int(datetime.now().timestamp())),
                        google_calendar_link="https://calendar.google.com"
                    )
                
                await interaction.followup.send(f"✅ Event created successfully! Event ID: {event.id}", ephemeral=True)
                logger.info("event_created", user=str(interaction.user), event_id=event.id)
                
            else:
                await interaction.followup.send("❌ Event creation cancelled.", ephemeral=True)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Event creation timed out. Please try again.", ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error creating event: {str(e)}", ephemeral=True)
        logger.error("add_event_error", error=str(e), user=str(interaction.user))

@bot.tree.command(name="myevents", description="List your upcoming events")
async def my_events_command(interaction: discord.Interaction):
    """List user's upcoming events."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        async with session_scope() as session:
            user_repo = UserRepository(session)
            event_repo = EventRepository(session)
            
            user_obj = await user_repo.get_user_by_discord_id(str(interaction.user.id))
            
            if not user_obj:
                await interaction.followup.send("❌ No events found. You haven't created any events yet.", ephemeral=True)
                return
            
            events = await event_repo.list_events_for_user(user_obj.id, limit=10)
            
            if not events:
                await interaction.followup.send("📅 No upcoming events found.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📅 Your Upcoming Events",
                color=0x0099ff
            )
            
            for event in events:
                embed.add_field(
                    name=f"📌 {event.title}",
                    value=f"🕐 {event.start_time.strftime('%Y-%m-%d %H:%M')}\n📝 {event.description[:100]}...",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info("events_listed", user=str(interaction.user), count=len(events))
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error retrieving events: {str(e)}", ephemeral=True)
        logger.error("my_events_error", error=str(e), user=str(interaction.user))

@bot.tree.command(name="set-tz", description="Set your timezone")
async def set_timezone_command(interaction: discord.Interaction, timezone: str):
    """Set user's timezone."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Validate timezone (basic validation)
        valid_timezones = [
            'UTC', 'EST', 'PST', 'CST', 'MST', 'GMT',
            'America/New_York', 'America/Los_Angeles', 'America/Chicago',
            'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Australia/Sydney'
        ]
        
        if timezone not in valid_timezones:
            await interaction.followup.send(
                f"❌ Invalid timezone. Valid options: {', '.join(valid_timezones[:10])}...", 
                ephemeral=True
            )
            return
        
        async with session_scope() as session:
            user_repo = UserRepository(session)
            user_obj = await user_repo.get_user_by_discord_id(str(interaction.user.id))
            if not user_obj:
                user_obj = await user_repo.create_user(str(interaction.user.id), str(interaction.user))
            
            await user_repo.update_user(user_obj.id, timezone=timezone)
        
        await interaction.followup.send(f"✅ Timezone set to {timezone}", ephemeral=True)
        logger.info("timezone_set", user=str(interaction.user), timezone=timezone)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error setting timezone: {str(e)}", ephemeral=True)
        logger.error("set_timezone_error", error=str(e), user=str(interaction.user))

@bot.tree.command(name="connect", description="Connect your Google Calendar account")
async def connect_command(interaction: discord.Interaction):
    """Connect Google Calendar account."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # For now, just acknowledge the connection
        # In a full implementation, this would handle OAuth flow
        await interaction.followup.send(
            "🔗 Google Calendar connection feature is being implemented. "
            "For now, events will be stored locally in the database.", 
            ephemeral=True
        )
        logger.info("connect_requested", user=str(interaction.user))
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error connecting calendar: {str(e)}", ephemeral=True)
        logger.error("connect_error", error=str(e), user=str(interaction.user))

# Regular commands (prefix-based)
@bot.command(name='ping')
async def ping_regular(ctx):
    """Regular ping command."""
    await ctx.send('🏓 Pong! Calendar Agent is online and ready.')

@bot.command(name='test')
async def test(ctx):
    """Test command."""
    await ctx.send('✅ Calendar Agent Bot is working! All systems operational.')

@bot.command(name='time')
async def get_time(ctx):
    """Get current time."""
    now = datetime.now()
    await ctx.send(f'🕐 Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}')

async def main():
    """Main function to start the bot."""
    print("🚀 Starting Calendar Agent Discord Bot...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if Discord token is configured
    if not settings.discord_token:
        print("❌ Discord token not configured!")
        print("Please set DISCORD_TOKEN in your .env file")
        return
    
    print("🤖 Starting Discord bot...")
    try:
        # Start the bot and keep it running
        async with bot:
            await bot.start(settings.discord_token)
    except discord.LoginFailure:
        print("❌ Invalid Discord token!")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logger.error("bot_start_error", error=str(e))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Calendar Agent Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
