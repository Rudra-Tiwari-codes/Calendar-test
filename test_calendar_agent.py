#!/usr/bin/env python3
"""
Comprehensive test script for Calendar Agent
This script tests all the core functionality of the Calendar Agent.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_datetime, parse_natural_range, extract_event_details
from events_agent.infra.settings import settings
from events_agent.infra.db import db_ping, get_engine
from events_agent.domain.models import Base
from events_agent.infra.logging import configure_logging, get_logger


async def test_database_connection():
    """Test database connection."""
    print("🔍 Testing database connection...")
    try:
        is_connected = await db_ping()
        if is_connected:
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database connection failed!")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


async def test_natural_language_parsing():
    """Test natural language date parsing."""
    print("\n🔍 Testing natural language date parsing...")
    
    test_cases = [
        ("tomorrow 3pm", "Should parse to tomorrow at 3 PM"),
        ("next monday 2pm", "Should parse to next Monday at 2 PM"),
        ("in 2 hours", "Should parse to 2 hours from now"),
        ("december 25th 10am", "Should parse to December 25th at 10 AM"),
        ("today 5pm", "Should parse to today at 5 PM"),
    ]
    
    success_count = 0
    for text, description in test_cases:
        try:
            result = parse_natural_datetime(text)
            print(f"✅ '{text}' -> {result.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            success_count += 1
        except Exception as e:
            print(f"❌ '{text}' failed: {e}")
    
    print(f"📊 Natural language parsing: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)


def test_event_details_extraction():
    """Test event details extraction from natural language."""
    print("\n🔍 Testing event details extraction...")
    
    test_cases = [
        ("Team meeting tomorrow 3pm with @john @jane", "Should extract title, time, and attendees"),
        ("Lunch with Sarah next Friday 12pm at the cafe", "Should extract title, time, and location"),
        ("Project review meeting tomorrow 2-4pm in conference room A", "Should extract title and time range"),
    ]
    
    success_count = 0
    for text, description in test_cases:
        try:
            result = extract_event_details(text)
            print(f"✅ '{text}'")
            print(f"   Title: {result['title']}")
            print(f"   Time: {result['time']}")
            print(f"   Attendees: {result['attendees']}")
            success_count += 1
        except Exception as e:
            print(f"❌ '{text}' failed: {e}")
    
    print(f"📊 Event details extraction: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)


def test_settings_loading():
    """Test settings loading from environment."""
    print("\n🔍 Testing settings loading...")
    
    required_settings = [
        'discord_token',
        'database_url',
        'google_client_id',
        'google_client_secret',
        'fernet_key'
    ]
    
    success_count = 0
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if value:
            print(f"✅ {setting}: {'*' * 10} (configured)")
            success_count += 1
        else:
            print(f"❌ {setting}: Not configured")
    
    print(f"📊 Settings loading: {success_count}/{len(required_settings)} settings configured")
    return success_count == len(required_settings)


async def test_database_models():
    """Test database models creation."""
    print("\n🔍 Testing database models...")
    try:
        engine = get_engine()
        
        # Test that we can create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database models created successfully!")
        return True
    except Exception as e:
        print(f"❌ Database models error: {e}")
        return False


async def test_google_calendar_credentials():
    """Test Google Calendar credentials file."""
    print("\n🔍 Testing Google Calendar credentials...")
    
    credentials_file = "client_secret.json"
    if os.path.exists(credentials_file):
        print(f"✅ Google credentials file found: {credentials_file}")
        
        # Try to read the file
        try:
            import json
            with open(credentials_file, 'r') as f:
                creds = json.load(f)
            
            if 'web' in creds and 'client_id' in creds['web']:
                print("✅ Google credentials file is valid!")
                return True
            else:
                print("❌ Google credentials file format is invalid!")
                return False
        except Exception as e:
            print(f"❌ Error reading Google credentials: {e}")
            return False
    else:
        print(f"❌ Google credentials file not found: {credentials_file}")
        return False


def test_discord_token():
    """Test Discord bot token format."""
    print("\n🔍 Testing Discord bot token...")
    
    token = settings.discord_token
    if token and len(token) > 50 and '.' in token:
        print("✅ Discord bot token format looks valid!")
        return True
    else:
        print("❌ Discord bot token format is invalid!")
        return False


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Calendar Agent Tests")
    print("=" * 50)
    
    # Configure logging
    configure_logging()
    
    # Run tests
    tests = [
        ("Settings Loading", test_settings_loading),
        ("Discord Token", test_discord_token),
        ("Google Calendar Credentials", test_google_calendar_credentials),
        ("Database Connection", test_database_connection),
        ("Database Models", test_database_models),
        ("Natural Language Parsing", test_natural_language_parsing),
        ("Event Details Extraction", test_event_details_extraction),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Calendar Agent is ready to run!")
        print("\n📋 Next steps:")
        print("1. Run: uv run python -m events_agent.main")
        print("2. Test Discord commands in your server")
        print("3. Use /connect to link Google Calendar")
        print("4. Use /addevent to create events")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before running the bot.")
    
    return passed == len(results)


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
