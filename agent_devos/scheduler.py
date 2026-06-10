"""Scheduler — priority-aware task dispatcher.

Picks the next ready task from the DAG using priority scoring.
Execution is atomic: snapshot → execute → validate → commit FSM
On failure: rollback to snapshot, mark failed, invoke recovery.
"""

from __future__ import annotations

import sys
sys.path.insert(0, "/mnt/c/Users/Linsa/ai-factory-runtime")
from ai_runtime.task import Task, TaskStatus
from ai_runtime.graph import TaskGraph
from ai_runtime.fsm import transition, can_transition

from agent_devos.dag_builder import TaskMeta
from agent_devos.priority import compute_priority


class Scheduler:
    """Priority-aware scheduler that dispatches ready tasks from a TaskGraph."""

    def __init__(self, graph: TaskGraph, metas: dict[str, TaskMeta]) -> None:
        self.graph = graph
        self.metas = metas
        self.execution_count: dict[str, int] = {}

    def next_ready(self) -> tuple[Task | None, TaskMeta | None]:
        """Return the highest-priority ready task and its metadata.
        Returns (None, None) if no tasks are ready.
        """
        ready_tasks = self.graph.ready_tasks()
        if not ready_tasks:
            return None, None

        scored: list[tuple[int, Task, TaskMeta]] = []
        for task in ready_tasks:
            meta = self.metas.get(task.id)
            if meta is None:
                continue
            score = compute_priority(
                meta, task.status,
                retry_count=task.retry_count,
            )
            scored.append((score, task, meta))

        if not scored:
            return None, None

        scored.sort(key=lambda x: x[0], reverse=True)
        _, best_task, best_meta = scored[0]
        return best_task, best_meta

    def dispatch(self, task: Task) -> None:
        """Mark a task as DISPATCHED (pre-execution gate)."""
        if not can_transition(task, TaskStatus.DISPATCHED):
            raise ValueError(f"Cannot dispatch task {task.id} in status {task.status.value}")
        transition(task, TaskStatus.DISPATCHED)

    def mark_running(self, task: Task) -> None:
        """Mark a task as RUNNING."""
        if not can_transition(task, TaskStatus.RUNNING):
            raise ValueError(f"Cannot run task {task.id} in status {task.status.value}")
        transition(task, TaskStatus.RUNNING)
        self.execution_count[task.id] = self.execution_count.get(task.id, 0) + 1

    def mark_passed(self, task: Task) -> None:
        """Mark a task as PASSED."""
        if not can_transition(task, TaskStatus.PASSED):
            raise ValueError(f"Cannot pass task {task.id} in status {task.status.value}")
        transition(task, TaskStatus.PASSED)

    def mark_failed(self, task: Task, reason: str = "") -> None:
        """Mark a task as FAILED."""
        if not can_transition(task, TaskStatus.FAILED):
            raise ValueError(f"Cannot fail task {task.id} in status {task.status.value}")
        transition(task, TaskStatus.FAILED, reason=reason)

    def mark_human_required(self, task: Task, reason: str = "") -> None:
        """Mark a task as HUMAN_REQUIRED (escalation)."""
        if not can_transition(task, TaskStatus.HUMAN_REQUIRED):
            raise ValueError(f"Cannot escalate task {task.id} in status {task.status.value}")
        transition(task, TaskStatus.HUMAN_REQUIRED, reason=reason)

    def is_done(self) -> bool:
        """Return True if all tasks are PASSED or CANCELLED."""
        return self.graph.all_passed()

    def is_blocked(self) -> bool:
        """Return True if no tasks are ready and not all done."""
        return not self.is_done() and len(self.graph.ready_tasks()) == 0
