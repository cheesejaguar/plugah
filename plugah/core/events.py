"""
Minimal async event bus for publishing Event objects and subscribing via async generator.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from .models import Event


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[Event]] = []
        self._closed = False

    async def publish(self, event: Event) -> None:
        if self._closed:
            return
        for q in self._subscribers:
            # Use put_nowait to avoid blocking; if full, drop to keep demo flowing
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def subscribe(self) -> AsyncGenerator[Event, None]:
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self._subscribers.remove(queue)

    async def close(self) -> None:
        self._closed = True
        # Drain subscribers with a sentinel? For demo, just mark closed

