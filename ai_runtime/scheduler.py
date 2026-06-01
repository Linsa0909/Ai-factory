"""Scheduler: dispatches tasks from the graph. Does NOT own DAG logic."""

from ai_runtime.task import Task, TaskStatus
from ai_runtime.fsm import transition
from ai_runtime.graph import TaskGraph


class Scheduler:
    """Single-thread dispatcher. All DAG queries delegated to TaskGraph."""

    def __init__(self, graph: TaskGraph) -> None:
        self.graph = graph

    def next_ready(self) -> Task | None:
        """Return the next ready task (P0: pick first)."""
        ready = self.graph.ready_tasks()
        return ready[0] if ready else None

    @staticmethod
    def dispatch(task: Task) -> None:
        """Move task through READY → DISPATCHED → RUNNING."""
        transition(task, TaskStatus.READY)
        transition(task, TaskStatus.DISPATCHED)
        transition(task, TaskStatus.RUNNING)

    @staticmethod
    def mark_passed(task: Task) -> None:
        transition(task, TaskStatus.PASSED)

    @staticmethod
    def mark_failed(task: Task, reason: str) -> None:
        transition(task, TaskStatus.FAILED, reason=reason)

    @staticmethod
    def mark_human_required(task: Task, reason: str = "") -> None:
        transition(task, TaskStatus.HUMAN_REQUIRED, reason=reason)

    def is_done(self) -> bool:
        return self.graph.all_passed()
