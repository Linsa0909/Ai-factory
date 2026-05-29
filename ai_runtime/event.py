from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator
import asyncio


class EventType(str, Enum):
    TASK_STARTED = "task_started"
    TASK_PASSED = "task_passed"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    TASK_HUMAN_REQUIRED = "task_human_required"
    FIX_ATTEMPTED = "fix_attempted"
    FIX_CONVERGENCE_FAILED = "fix_convergence_failed"
    SCOPE_VIOLATION = "scope_violation"
    ROLLBACK_EXECUTED = "rollback_executed"
    GATE_PENDING = "gate_pending"
    PIPELINE_DONE = "pipeline_done"


@dataclass
class Event:
    type: EventType
    task_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    """asyncio.Queue based event bus. P0: no merge/debounce/priority."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers: list[asyncio.Queue[Event]] = []

    async def emit(self, event: Event) -> None:
        await self._queue.put(event)
        for sub in self._subscribers:
            await sub.put(event)

    async def subscribe(self) -> AsyncIterator[Event]:
        """Return an async iterator of events. Caller creates a subscription."""
        q: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers.append(q)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            self._subscribers.remove(q)

    async def next_event(self) -> Event:
        """Block until the next event arrives."""
        return await self._queue.get()
