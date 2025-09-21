#!/usr/bin/env python3
"""
Quick integration test script for Calendar Agent
Run this to verify Discord bot, database, and basic functionality work
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_integration():
    """Test all major components"""
    print("🧪 Calendar Agent Integration Test")
    print("=" * 40)
    
    # Test 1: Environment Variables
    print("\n1. Testing Environment Variables...")
    discord_token = os.getenv('DISCORD_TOKEN')
    database_url = os.getenv('DATABASE_URL')
    
    if not discord_token:
        print("❌ DISCORD_TOKEN not found in .env")
        return False
    else:
        print(f"✅ Discord token found (ends with: ...{discord_token[-10:]})")
    
    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    else:
        print(f"✅ Database URL found: {database_url[:30]}...")
    
    # Test 2: Database Connection
    print("\n2. Testing Database Connection...")
    try:
        from events_agent.infra.db import get_engine, get_session_factory
        from events_agent.domain.models import Base
        
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database connection successful, tables created")
        
        # Test database query
        session_factory = get_session_factory()
        async with session_factory() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            print("✅ Database query test successful")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 3: Discord Bot Import
    print("\n3. Testing Discord Bot...")
    try:
        from events_agent.bot.discord_bot import build_bot
        bot = build_bot()
        print("✅ Discord bot creation successful")
    except Exception as e:
        print(f"❌ Discord bot creation failed: {e}")
        return False
    
    # Test 4: Natural Language Parsing
    print("\n4. Testing Natural Language Parsing...")
    try:
        from events_agent.infra.date_parsing import parse_natural_datetime
        result = parse_natural_datetime("tomorrow 3pm")
        print(f"✅ Date parsing successful: {result}")
    except Exception as e:
        print(f"❌ Date parsing failed: {e}")
        return False
    
    # Test 5: Google Calendar Service
    print("\n5. Testing Google Calendar Service...")
    try:
        from events_agent.services.calendar_service import GoogleCalendarService
        print("✅ Google Calendar service import successful")
    except Exception as e:
        print(f"❌ Google Calendar service failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 All tests passed! Your integration is working.")
    print("\nNext steps:")
    print("1. Run: python run_bot.py")
    print("2. Test slash commands in Discord")
    print("3. Try: /addevent tomorrow 3pm Test event")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_integration())