import asyncio
import json

import pytest

from plugah.core.events import EventBus
from plugah.core.models import Event, EventType


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()

    async def produce():
        await bus.publish(Event(type=EventType.PHASE_CHANGE, text="startup"))
        await bus.publish(Event(type=EventType.QUESTION, text="Who?"))

    events = []

    async def consume():
        async for ev in bus.subscribe():
            events.append(ev)
            if len(events) == 2:
                break

    await asyncio.gather(produce(), consume())
    assert len(events) == 2
    line = events[0].to_ndjson()
    data = json.loads(line)
    assert data["type"] == "PHASE_CHANGE"

