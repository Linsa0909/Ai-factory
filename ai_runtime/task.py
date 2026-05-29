from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    PAUSED = "paused"
    WAITING_RETRY = "waiting_retry"
    FIXING = "fixing"
    VERIFYING = "verifying"
    ROLLBACK_PENDING = "rollback_pending"
    ROLLING_BACK = "rolling_back"
    HUMAN_REQUIRED = "human_required"
    BLOCKED = "blocked"
    STALE = "stale"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    type: str
    module: str = ""
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)

    retry_count: int = 0
    max_retry: int = 3
    timeout_seconds: int = 1800
    model: str = ""

    status_history: list[str] = field(default_factory=list)
    failure_reason: str = ""
    snapshot_before: str = ""
    snapshot_after: str = ""
    outputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "type": self.type, "module": self.module,
            "status": self.status.value, "depends_on": self.depends_on,
            "retry_count": self.retry_count, "max_retry": self.max_retry,
            "status_history": self.status_history,
            "failure_reason": self.failure_reason,
            "snapshot_before": self.snapshot_before,
            "outputs": self.outputs,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Task:
        return cls(
            id=d["id"], type=d["type"], module=d.get("module", ""),
            status=TaskStatus(d.get("status", "pending")),
            depends_on=d.get("depends_on", []),
            retry_count=d.get("retry_count", 0),
            max_retry=d.get("max_retry", 3),
            status_history=d.get("status_history", []),
            failure_reason=d.get("failure_reason", ""),
            snapshot_before=d.get("snapshot_before", ""),
            outputs=d.get("outputs", []),
        )
