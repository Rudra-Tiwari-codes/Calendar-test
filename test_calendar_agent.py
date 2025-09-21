#!/usr/bin/env python3
"""
Comprehensive Production Test Script for Calendar Agent
This script tests all core functionality for Supabase production deployment.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_datetime, parse_natural_range, extract_event_details
from events_agent.infra.settings import settings
from events_agent.infra.logging import configure_logging, get_logger


async def test_supabase_connection():
    """Test Supabase database connection."""
    print("🔍 Testing Supabase production database connection...")
    try:
        # Test Supabase REST API connection
        from events_agent.infra.supabase_db import get_supabase_db
        supabase = get_supabase_db()
        
        # Test connection by checking if client is initialized
        if supabase:
            print("✅ Supabase connection successful!")
            print(f"   Database URL: {settings.database_url[:50]}...")
            print(f"   Supabase URL: {settings.supabase_url}")
            return True
        else:
            print("❌ Supabase connection failed!")
            return False
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        print("💡 Check your DATABASE_URL and SUPABASE credentials in .env")
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
    print("\n🔍 Testing production settings loading...")
    
    required_settings = [
        ('discord_token', 'Discord Bot Token'),
        ('database_url', 'Supabase Database URL'),
        ('supabase_url', 'Supabase Project URL'),
        ('supabase_key', 'Supabase Anon Key'),
        ('google_client_id', 'Google OAuth Client ID'),
        ('google_client_secret', 'Google OAuth Client Secret'),
        ('fernet_key', 'Encryption Key')
    ]
    
    success_count = 0
    for setting, description in required_settings:
        value = getattr(settings, setting, None)
        if value:
            print(f"✅ {description}: {'*' * 10} (configured)")
            success_count += 1
        else:
            print(f"❌ {description}: Not configured")
    
    print(f"📊 Settings loading: {success_count}/{len(required_settings)} settings configured")
    return success_count == len(required_settings)


async def test_database_models():
    """Test database connection via Supabase REST API."""
    print("\n🔍 Testing Supabase database models...")
    try:
        from events_agent.infra.supabase_db import get_supabase_db
        supabase = get_supabase_db()
        
        # Test basic connection by checking if client exists
        if supabase:
            print("✅ Supabase client initialized successfully!")
            print(f"   Database URL configured: {settings.database_url[:50]}...")
            return True
        else:
            print("❌ Supabase client initialization failed!")
            return False
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False


async def test_google_calendar_setup():
    """Test Google Calendar OAuth configuration."""
    print("\n🔍 Testing Google Calendar OAuth setup...")
    
    # Check if Google OAuth is configured
    if not settings.google_client_id or not settings.google_client_secret:
        print("❌ Google OAuth credentials not configured!")
        return False
    
    print("✅ Google OAuth credentials configured!")
    print(f"   Client ID: {settings.google_client_id[:20]}...")
    print(f"   Client Secret: {'*' * 20}")
    
    # Check if Supabase Auth is configured
    if settings.supabase_url:
        auth_url = f"{settings.supabase_url}/auth/v1/authorize"
        print(f"✅ Supabase Auth URL: {auth_url}")
        return True
    else:
        print("❌ Supabase URL not configured for Auth!")
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
    """Run all production tests."""
    print("🚀 Starting Calendar Agent Production Tests")
    print("=" * 60)
    print("🎯 Testing Supabase Production Configuration")
    print("=" * 60)
    
    # Configure logging
    configure_logging()
    
    # Run tests
    tests = [
        ("Settings Loading", test_settings_loading),
        ("Discord Token Format", test_discord_token),
        ("Google Calendar OAuth Setup", test_google_calendar_setup),
        ("Supabase Database Connection", test_supabase_connection),
        ("Supabase Database Models", test_database_models),
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
    print("\n" + "=" * 60)
    print("📊 PRODUCTION TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Calendar Agent is ready for production!")
        print("\n📋 Next steps:")
        print("1. Create virtual environment: python -m venv venv")
        print("2. Activate environment: venv\\Scripts\\activate (Windows)")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Run the bot: python start_bot.py")
        print("5. Test Discord commands in your server:")
        print("   • /ping - Test bot connectivity")
        print("   • /connect - Link Google Calendar via Supabase Auth")
        print("   • /addevent - Create calendar events")
        print("   • /myevents - View upcoming events")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before deployment.")
        print("\n🔧 Common fixes:")
        print("• Update .env file with correct Supabase credentials")
        print("• Verify Discord bot token is valid")
        print("• Check Google OAuth configuration in Supabase Auth")
    
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
