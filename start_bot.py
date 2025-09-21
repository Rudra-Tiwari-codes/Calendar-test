#!/usr/bin/env python3
"""
Simple working launcher for Calendar Agent
"""

import sys
import os
import asyncio
import signal
from datetime import datetime


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print('\n🛑 Shutting down Calendar Agent...')
    sys.exit(0)

async def main():
    """Main function to start the bot."""
    print("🚀 Starting Calendar Agent...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Import and configure logging
        from events_agent.infra.logging import configure_logging, get_logger
        configure_logging()
        logger = get_logger()
        logger.info("calendar_agent_starting")
        
        # Import settings
        from events_agent.infra.settings import settings
        print(f"📡 HTTP Server will run on: http://{settings.http_host}:{settings.http_port}")
        print(f"🤖 Discord Bot Token: {'✅ Configured' if settings.discord_token else '❌ Missing'}")
        
        # Import Discord bot
        from events_agent.bot.discord_bot import build_bot
        print("🔧 Building Discord bot...")
        discord_client = build_bot()
        
        # Start Discord bot
        print("🤖 Starting Discord bot...")
        if not settings.discord_token:
            print("❌ Discord token not configured!")
            return
        
        # Start the bot
        await discord_client.start(settings.discord_token)
        
    except Exception as e:
        print(f"❌ Error starting Calendar Agent: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Calendar Agent stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
