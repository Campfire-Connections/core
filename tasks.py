"""
Lightweight task shims to isolate side effects and ease a future move to Celery/RQ.
Currently executes synchronously; swap `run_async` to queue later.
"""

import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def run_async(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a callable now; placeholder for async task runner.
    """
    logger.info("task.dispatch", extra={"task": func.__name__})
    return func(*args, **kwargs)
