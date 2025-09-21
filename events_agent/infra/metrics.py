from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter


registry = CollectorRegistry()

events_created_total = Counter("events_created_total", "Number of events created", registry=registry)
reminders_sent_total = Counter("reminders_sent_total", "Number of reminders sent", registry=registry)
gcal_errors_total = Counter("gcal_errors_total", "Number of Google Calendar errors", registry=registry)


