#!/usr/bin/env python3
"""
Simple integration test without pydantic dependencies
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_basic():
    """Test basic functionality without complex dependencies"""
    print("🧪 Calendar Agent Basic Test")
    print("=" * 40)
    
    # Test 1: Environment Variables
    print("\n1. Testing Environment Variables...")
    discord_token = os.getenv('DISCORD_TOKEN')
    database_url = os.getenv('DATABASE_URL')
    
    if discord_token:
        print(f"✅ Discord token found")
    else:
        print("❌ DISCORD_TOKEN not found")
    
    if database_url:
        print(f"✅ Database URL found: {database_url}")
    else:
        print("❌ DATABASE_URL not found")
    
    # Test 2: Basic imports
    print("\n2. Testing Basic Imports...")
    try:
        import discord
        print("✅ Discord.py imported successfully")
    except Exception as e:
        print(f"❌ Discord.py import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
    except Exception as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import dateparser
        print("✅ DateParser imported successfully")
    except Exception as e:
        print(f"❌ DateParser import failed: {e}")
        return False
    
    # Test 3: Date parsing functionality
    print("\n3. Testing Date Parsing...")
    try:
        result = dateparser.parse("tomorrow 3pm")
        print(f"✅ Date parsing works: {result}")
    except Exception as e:
        print(f"❌ Date parsing failed: {e}")
        return False
    
    # Test 4: Database connection (SQLite only)
    print("\n4. Testing SQLite Database...")
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine("sqlite:///test.db")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ SQLite database connection successful")
    except Exception as e:
        print(f"❌ SQLite database connection failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 Basic integration test passed!")
    print("\nYour core dependencies are working.")
    print("Next: Add your real Discord token and Supabase credentials to .env")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_basic())