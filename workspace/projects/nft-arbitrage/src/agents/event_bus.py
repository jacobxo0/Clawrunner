"""
Simple in-process async event bus for agent communication.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

Callback = Callable[[Any], Coroutine]


class EventBus:
    """Publish/subscribe event bus with async callbacks."""

    def __init__(self):
        self._subscribers: dict[str, list[Callback]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callback) -> None:
        self._subscribers[event_type].append(callback)
        logger.debug("Subscribed %s to event '%s'", callback.__name__, event_type)

    async def publish(self, event_type: str, data: Any = None) -> None:
        callbacks = self._subscribers.get(event_type, [])
        if not callbacks:
            return
        logger.debug("Publishing event '%s' to %d subscribers", event_type, len(callbacks))
        await asyncio.gather(
            *(cb(data) for cb in callbacks),
            return_exceptions=True,
        )
