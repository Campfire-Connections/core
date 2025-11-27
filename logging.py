"""
Structured logging helpers for domain events.
"""

import logging
from typing import Optional, Mapping, Any


def log_event(
    action: str,
    *,
    actor_id: Optional[int] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    Emit a structured event log with a consistent shape.
    """
    logger = logging.getLogger("campfire.events")
    payload = {"action": action}
    if actor_id is not None:
        payload["actor_id"] = actor_id
    if extra:
        payload.update(extra)
    logger.info(action, extra=payload)
