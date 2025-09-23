#!/usr/bin/env python3
"""
Test Google Calendar API integration
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

from events_agent.adapters.gcal import create_event, list_events
from events_agent.infra.settings import settings


async def test_google_calendar_api():
    """Test Google Calendar OAuth configuration via Supabase."""
    print("🔍 Testing Google Calendar API Integration via Supabase")
    print("=" * 50)
    
    # Check if Supabase OAuth is configured
    if not settings.supabase_url:
        print("❌ Supabase URL not configured")
        return False
    
    print(f"✅ Supabase URL configured: {settings.supabase_url}")
    
    # Check if Google OAuth is configured in environment (for Supabase Auth)
    if not settings.google_client_id or not settings.google_client_secret:
        print("⚠️ Google OAuth credentials not in environment")
        print("   These should be configured in Supabase Auth → Providers → Google")
        print("   Not in your .env file for Supabase OAuth")
    else:
        print("ℹ️ Google OAuth credentials found in environment")
        print("   For Supabase OAuth, these should be configured in Supabase dashboard instead")
    
    # Test OAuth flow (simplified)
    print("\n🔍 Testing Supabase OAuth Configuration...")
    print(f"   Supabase URL: {settings.supabase_url}")
    print("   OAuth handled by Supabase - no manual redirect URI needed")
    
    if settings.supabase_url:
        print("✅ Supabase OAuth configured")
    else:
        print("❌ Supabase OAuth settings missing")
        return False
    
    print("\n📋 To test Google Calendar integration:")
    print("1. Start the bot: uv run python -m events_agent.main")
    print("2. In Discord, use: /connect")
    print("3. Click the link to authorize Google Calendar")
    print("4. Use: /addevent title:Test Event time:tomorrow 3pm")
    print("5. Check your Google Calendar for the event")
    
    return True


def test_discord_bot():
    """Test Discord bot configuration."""
    print("\n🔍 Testing Discord Bot Configuration")
    print("=" * 50)
    
    token = settings.discord_token
    if token and len(token) > 50:
        print("✅ Discord bot token configured")
        print(f"   Token length: {len(token)} characters")
        print(f"   Token format: {'Valid' if '.' in token else 'Invalid'}")
    else:
        print("❌ Discord bot token not configured or invalid")
        return False
    
    print("\n📋 To test Discord bot:")
    print("1. Make sure your bot is invited to a Discord server")
    print("2. Start the bot: uv run python -m events_agent.main")
    print("3. In Discord, use: /ping")
    print("4. You should see 'Pong! Bot is online and ready.'")
    
    return True


async def main():
    """Run all tests."""
    print("🚀 Google Calendar API Test")
    print("=" * 50)
    
    # Test Google Calendar API
    gcal_ok = await test_google_calendar_api()
    
    # Test Discord bot
    discord_ok = test_discord_bot()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    if gcal_ok and discord_ok:
        print("🎉 All configurations look good!")
        print("\n🚀 Ready to test the full application:")
        print("1. Run: uv run python -m events_agent.main")
        print("2. Test Discord commands")
        print("3. Connect Google Calendar")
        print("4. Create events")
    else:
        print("⚠️  Some configurations need attention")
        if not gcal_ok:
            print("   - Fix Google Calendar API setup")
        if not discord_ok:
            print("   - Fix Discord bot token")
    
    print(f"\n📁 Database will store data in: {os.path.abspath('events_agent.db')}")
    print("💡 Events created via Discord will appear in both:")
    print("   - Your Google Calendar (via API)")
    print("   - Supabase PostgreSQL database (for reminders and tracking)")


if __name__ == "__main__":
    asyncio.run(main())
