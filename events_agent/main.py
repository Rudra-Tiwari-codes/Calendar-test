from __future__ import annotations

import asyncio
import uvicorn

from .app.http import create_app
from .bot.discord_bot_simple import build_bot
from .infra.logging import configure_logging, get_logger
from .infra.settings import settings
from .infra.scheduler import start_scheduler, set_reminder_service
from .infra.db import get_engine
from .domain.models import Base
from .services.reminder_service import ReminderService


async def main_async() -> None:
    configure_logging()
    logger = get_logger()
    logger.info("starting_calendar_agent")

    # Initialize Supabase for production database
    logger.info("initializing_supabase_production_db")
    try:
        from .infra.supabase_db import get_supabase_db
        get_supabase_db()
        logger.info("supabase_production_db_initialized")
    except Exception as e:
        logger.error("supabase_production_db_failed", error=str(e))
        # Don't raise - allow the HTTP server to start for health checks
        logger.warning("continuing_without_supabase_for_health_checks")

    # Create FastAPI app
    app = create_app()
    
    # Build Discord bot (but don't fail if token is missing)
    discord_client = None
    try:
        discord_client = build_bot()
    except Exception as e:
        logger.error("discord_bot_build_failed", error=str(e))
        logger.warning("continuing_without_discord_bot_for_health_checks")
    
    # Create reminder service with Discord client
    reminder_service = None
    if discord_client:
        reminder_service = ReminderService(discord_client)
        set_reminder_service(reminder_service)
    
    # Start scheduler
    scheduler = start_scheduler()
    # Start the scheduler now that we have an event loop
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler_started_in_main")

    async def run_uvicorn() -> None:
        """Run the FastAPI server."""
        logger.info("configuring_uvicorn_server", host=settings.http_host, port=settings.http_port)
        config = uvicorn.Config(app, host=settings.http_host, port=settings.http_port, log_config=None)
        server = uvicorn.Server(config)
        logger.info("starting_http_server", host=settings.http_host, port=settings.http_port)
        print(f"Health check endpoint: http://{settings.http_host}:{settings.http_port}/healthz")
        await server.serve()

    async def run_discord() -> None:
        """Run the Discord bot."""
        if not discord_client:
            logger.warning("discord_client_not_available_skipping")
            return
            
        token = settings.discord_token
        if not token:
            logger.warning("discord_token_missing")
            return
        
        logger.info("starting_discord_bot")
        await discord_client.start(token)

    # Run both services concurrently
    try:
        print("Starting Calendar Agent...")
        print(f"Environment: {settings.environment}")
        print(f"HTTP Server: http://{settings.http_host}:{settings.http_port}")
        print(f"Health Check: http://{settings.http_host}:{settings.http_port}/healthz")
        print("Discord Bot: Starting...")
        # Use asyncio.gather instead of TaskGroup for compatibility
        await asyncio.gather(
            run_uvicorn(),
            run_discord(),
            return_exceptions=True
        )
    except Exception as e:
        logger.error("service_error", error=str(e))
        print(f"Error: {e}")
        raise
    finally:
        logger.info("shutting_down")
        scheduler.shutdown()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nShutting down Calendar Agent...")
    except Exception as e:
        print(f"Error starting Calendar Agent: {e}")
        raise


if __name__ == "__main__":
    main()


