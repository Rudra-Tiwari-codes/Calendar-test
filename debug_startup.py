#!/usr/bin/env python3
"""
Debug startup script to identify issues
"""

import sys
import os


def test_imports():
    """Test all imports step by step."""
    print("🔍 Testing imports...")
    
    try:
        print("1. Testing basic imports...")
        import asyncio
        import uvicorn
        print("✅ Basic imports OK")
        
        print("2. Testing events_agent imports...")
        from events_agent.infra.settings import settings
        print("✅ Settings import OK")
        
        print("3. Testing logging...")
        from events_agent.infra.logging import configure_logging, get_logger
        configure_logging()
        logger = get_logger()
        print("✅ Logging OK")
        
        print("4. Testing FastAPI app...")
        from events_agent.app.http import create_app
        app = create_app()
        print("✅ FastAPI app OK")
        
        print("5. Testing Discord bot...")
        from events_agent.bot.discord_bot import build_bot
        discord_client = build_bot()
        print("✅ Discord bot OK")
        
        print("6. Testing services...")
        from events_agent.services.reminder_service import ReminderService
        reminder_service = ReminderService(discord_client)
        print("✅ Reminder service OK")
        
        print("7. Testing scheduler...")
        from events_agent.infra.scheduler import start_scheduler, set_reminder_service
        set_reminder_service(reminder_service)
        scheduler = start_scheduler()
        print("✅ Scheduler OK")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings():
    """Test settings configuration."""
    print("\n🔍 Testing settings...")
    
    try:
        from events_agent.infra.settings import settings
        
        print(f"Discord token: {'✅ Set' if settings.discord_token else '❌ Missing'}")
        print(f"Database URL: {'✅ Set' if settings.database_url else '❌ Missing'}")
        print(f"Google Client ID: {'✅ Set' if settings.google_client_id else '❌ Missing'}")
        print(f"Google Client Secret: {'✅ Set' if settings.google_client_secret else '❌ Missing'}")
        print(f"Fernet Key: {'✅ Set' if settings.fernet_key else '❌ Missing'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

async def test_async_startup():
    """Test async startup components."""
    print("\n🔍 Testing async startup...")
    
    try:
        from events_agent.infra.settings import settings
        from events_agent.infra.logging import configure_logging, get_logger
        from events_agent.app.http import create_app
        from events_agent.bot.discord_bot import build_bot
        
        configure_logging()
        logger = get_logger()
        logger.info("debug_startup_test")
        
        app = create_app()
        discord_client = build_bot()
        
        print("✅ Async components initialized")
        return True
        
    except Exception as e:
        print(f"❌ Async startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests."""
    print("🚀 Calendar Agent Debug Startup")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test settings
    settings_ok = test_settings()
    
    # Test async startup
    import asyncio
    async_ok = asyncio.run(test_async_startup())
    
    print("\n" + "=" * 50)
    print("📊 DEBUG RESULTS")
    print("=" * 50)
    print(f"Imports: {'✅ OK' if imports_ok else '❌ FAILED'}")
    print(f"Settings: {'✅ OK' if settings_ok else '❌ FAILED'}")
    print(f"Async: {'✅ OK' if async_ok else '❌ FAILED'}")
    
    if imports_ok and settings_ok and async_ok:
        print("\n🎉 All tests passed! The application should start successfully.")
        print("\nTo start the bot, run:")
        print("uv run python -c \"import events_agent.main; events_agent.main.main()\"")
    else:
        print("\n⚠️ Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()
