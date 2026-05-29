import asyncio
from ai_runtime.event import Event, EventType, EventBus


async def test_emit_and_receive():
    bus = EventBus()
    await bus.emit(Event(type=EventType.TASK_STARTED, task_id="T1"))
    event = await bus.next_event()
    assert event.type == EventType.TASK_STARTED
    assert event.task_id == "T1"


async def test_subscribe_receives_events():
    bus = EventBus()
    received: list[Event] = []

    async def collect():
        async for event in bus.subscribe():
            received.append(event)
            if len(received) >= 2:
                break

    task = asyncio.create_task(collect())
    await asyncio.sleep(0.01)  # let subscriber register
    await bus.emit(Event(type=EventType.TASK_PASSED, task_id="T1"))
    await bus.emit(Event(type=EventType.TASK_FAILED, task_id="T2", payload={"reason": "test"}))
    await task
    assert len(received) == 2
    assert received[0].type == EventType.TASK_PASSED
    assert received[1].payload == {"reason": "test"}
