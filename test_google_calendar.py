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
    """Test Google Calendar API with your credentials."""
    print("🔍 Testing Google Calendar API Integration")
    print("=" * 50)
    
    # Check if credentials file exists
    credentials_file = "client_secret.json"
    if not os.path.exists(credentials_file):
        print(f"❌ Google credentials file not found: {credentials_file}")
        return False
    
    print(f"✅ Found credentials file: {credentials_file}")
    
    # Read credentials
    try:
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
        
        print("✅ Credentials file is valid JSON")
        print(f"   Client ID: {creds['web']['client_id']}")
        print(f"   Project ID: {creds['web']['project_id']}")
        
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False
    
    # Test OAuth flow (simplified)
    print("\n🔍 Testing OAuth Configuration...")
    print(f"   Client ID: {settings.google_client_id}")
    print(f"   Client Secret: {'*' * 20}")
    print(f"   Redirect URI: {settings.oauth_redirect_uri}")
    
    if settings.google_client_id and settings.google_client_secret:
        print("✅ OAuth settings configured")
    else:
        print("❌ OAuth settings missing")
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
    print("   - Local SQLite database (for reminders and tracking)")


if __name__ == "__main__":
    asyncio.run(main())
