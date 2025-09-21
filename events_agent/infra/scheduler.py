from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .metrics import reminders_sent_total
from .logging import get_logger


logger = get_logger().bind(service="scheduler")

# Global reminder service instance
_reminder_service = None


def set_reminder_service(reminder_service):
    """Set the reminder service instance."""
    global _reminder_service
    _reminder_service = reminder_service


async def _process_due_reminders() -> None:
    """Process due reminders using the reminder service."""
    try:
        if _reminder_service:
            await _reminder_service.process_due_reminders()
            reminders_sent_total.inc()
        else:
            logger.warning("reminder_service_not_available")
    except Exception as e:
        logger.error("process_due_reminders_failed", error=str(e))


def start_scheduler() -> AsyncIOScheduler:
    """Start the scheduler for processing reminders."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_process_due_reminders, IntervalTrigger(seconds=60))
    
    # Only start if we're in an event loop
    try:
        asyncio.get_running_loop()
        scheduler.start()
        logger.info("scheduler_started")
    except RuntimeError:
        # No event loop running, scheduler will start when event loop is available
        logger.info("scheduler_created_waiting_for_event_loop")
    
    return scheduler


