import asyncio
import json

import pytest

from plugah.core.events import EventBus
from plugah.core.models import Event, EventType


async def _wait_for_subscribers(bus: EventBus, count: int) -> None:
    # Subscription is lazy: the queue is registered on the generator's first step.
    for _ in range(100):
        if len(bus._subscribers) >= count:
            return
        await asyncio.sleep(0)
    raise AssertionError("subscriber never registered")


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    events: list[Event] = []

    async def consume():
        async for ev in bus.subscribe():
            events.append(ev)
            if len(events) == 2:
                break

    consumer = asyncio.create_task(consume())
    await _wait_for_subscribers(bus, 1)

    await bus.publish(Event(type=EventType.PHASE_CHANGE, text="startup"))
    await bus.publish(Event(type=EventType.QUESTION, text="Who?"))

    await asyncio.wait_for(consumer, timeout=5)

    assert [e.type for e in events] == [EventType.PHASE_CHANGE, EventType.QUESTION]
    assert [e.text for e in events] == ["startup", "Who?"]
    data = json.loads(events[0].to_ndjson())
    assert data["type"] == "PHASE_CHANGE"
    assert data["text"] == "startup"
    # Breaking out of the generator unregisters the subscriber
    assert bus._subscribers == []


@pytest.mark.asyncio
async def test_event_bus_fans_out_to_all_subscribers():
    bus = EventBus()
    got_a: list[str] = []
    got_b: list[str] = []

    async def consume(sink: list[str]):
        async for ev in bus.subscribe():
            sink.append(ev.text or "")
            break

    tasks = [asyncio.create_task(consume(got_a)), asyncio.create_task(consume(got_b))]
    await _wait_for_subscribers(bus, 2)
    await bus.publish(Event(type=EventType.PHASE_CHANGE, text="hello"))
    await asyncio.wait_for(asyncio.gather(*tasks), timeout=5)

    assert got_a == ["hello"]
    assert got_b == ["hello"]


@pytest.mark.asyncio
async def test_event_bus_drops_events_after_close():
    bus = EventBus()
    received: list[Event] = []

    async def consume():
        async for ev in bus.subscribe():
            received.append(ev)

    consumer = asyncio.create_task(consume())
    await _wait_for_subscribers(bus, 1)
    await bus.close()
    await bus.publish(Event(type=EventType.PHASE_CHANGE, text="ignored"))
    await asyncio.sleep(0.01)
    consumer.cancel()

    assert received == []
