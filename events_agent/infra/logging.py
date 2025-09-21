from __future__ import annotations

import logging
import sys
from typing import Any, Dict

import structlog


def _add_service(_: Any, __: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    # Preserve service if already provided; otherwise leave empty and let callers set it.
    event_dict.setdefault("service", "app")
    return event_dict


def _mask_secrets(_: Any, __: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    # Best-effort masking of common secret/token fields
    for key in list(event_dict.keys()):
        lower = str(key).lower()
        if any(s in lower for s in ["token", "secret", "password", "authorization"]):
            val = event_dict.get(key)
            if isinstance(val, str) and len(val) > 8:
                event_dict[key] = val[:4] + "…" + val[-2:]
            else:
                event_dict[key] = "***"
    return event_dict


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_service,
            _mask_secrets,
            timestamper,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(sort_keys=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    # Bridge stdlib logging into structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger():
    return structlog.get_logger()


