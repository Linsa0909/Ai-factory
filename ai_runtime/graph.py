"""TaskGraph: DAG of tasks. Owns add/query/invalidate. Scheduler delegates to this."""

from ai_runtime.task import Task, TaskStatus
from ai_runtime.fsm import transition, can_transition


class CyclicDependencyError(Exception):
    """Raised when adding a task would create a cycle in the DAG."""
    pass


class DanglingDependencyError(Exception):
    """Raised when a task depends on a non-existent task_id."""
    pass


class TaskGraph:
    """Directed Acyclic Graph of Tasks. Owns all DAG logic."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> None:
        """Register a task after validating its dependencies."""
        if task.id in self._tasks:
            raise ValueError(f"Duplicate task id: {task.id}")

        # Validate all deps exist (or will exist in same batch — we check lazily)
        # Check for direct self-dependency
        if task.id in task.depends_on:
            raise CyclicDependencyError(
                f"Task {task.id} cannot depend on itself"
            )

        self._tasks[task.id] = task

    def validate(self) -> None:
        """Validate the entire graph: no dangling deps, no cycles."""
        for task in self._tasks.values():
            for dep_id in task.depends_on:
                if dep_id not in self._tasks:
                    raise DanglingDependencyError(
                        f"Task {task.id} depends on {dep_id} which does not exist"
                    )
        self._check_cycles()

    def _check_cycles(self) -> None:
        """DFS-based cycle detection. Raises CyclicDependencyError if any cycle found."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {tid: WHITE for tid in self._tasks}

        def dfs(tid: str) -> None:
            color[tid] = GRAY
            for dep_id in self._tasks[tid].depends_on:
                if dep_id not in self._tasks:
                    continue  # validated elsewhere
                if color[dep_id] == GRAY:
                    raise CyclicDependencyError(
                        f"Cycle detected: {tid} \u2192 {dep_id}"
                    )
                if color[dep_id] == WHITE:
                    dfs(dep_id)
            color[tid] = BLACK

        for tid in self._tasks:
            if color[tid] == WHITE:
                dfs(tid)

    def get(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def all_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def ready_tasks(self) -> list[Task]:
        """Return tasks where all deps are PASSED and status is PENDING."""
        ready: list[Task] = []
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            if not task.depends_on:
                continue
            if all(
                self._tasks[dep_id].status == TaskStatus.PASSED
                for dep_id in task.depends_on
            ):
                ready.append(task)
        return ready

    def invalidate_downstream(self, upstream_id: str) -> list[Task]:
        """Mark all tasks that depend on upstream_id as STALE. Does NOT cascade further.

        Only tasks that allow a → STALE transition (PASSED, BLOCKED) are affected.
        Tasks in RUNNING, FAILED, or other states that don't permit STALE are silently skipped.
        """
        stale: list[Task] = []
        for task in self._tasks.values():
            if upstream_id not in task.depends_on:
                continue
            if task.status in (TaskStatus.STALE, TaskStatus.CANCELLED):
                continue
            if not can_transition(task, TaskStatus.STALE):
                continue
            transition(task, TaskStatus.STALE)
            stale.append(task)
        return stale

    def all_passed(self) -> bool:
        return all(t.status == TaskStatus.PASSED for t in self._tasks.values())

    def task_count(self) -> int:
        return len(self._tasks)
