"""FSM (Finite State Machine) transition engine for Task lifecycle.

This module is stateless — it validates and applies state transitions but owns no
mutable state itself. The sole dependency is the Task data model.
"""

from ai_runtime.task import Task, TaskStatus


# Allowed state transitions for every TaskStatus.
# Terminal states (PASSED, CANCELLED) have empty transition sets.
TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING:        {TaskStatus.READY, TaskStatus.CANCELLED},
    TaskStatus.READY:          {TaskStatus.DISPATCHED, TaskStatus.CANCELLED},
    TaskStatus.DISPATCHED:     {TaskStatus.RUNNING, TaskStatus.CANCELLED},
    TaskStatus.RUNNING:        {TaskStatus.PASSED, TaskStatus.FAILED, TaskStatus.TIMED_OUT, TaskStatus.PAUSED},
    TaskStatus.FAILED:         {TaskStatus.WAITING_RETRY, TaskStatus.ROLLBACK_PENDING, TaskStatus.HUMAN_REQUIRED, TaskStatus.BLOCKED},
    TaskStatus.TIMED_OUT:      {TaskStatus.WAITING_RETRY, TaskStatus.HUMAN_REQUIRED},
    TaskStatus.PAUSED:         {TaskStatus.READY, TaskStatus.CANCELLED},
    TaskStatus.WAITING_RETRY:  {TaskStatus.FIXING},
    TaskStatus.FIXING:         {TaskStatus.VERIFYING},
    TaskStatus.VERIFYING:      {TaskStatus.PASSED, TaskStatus.FAILED, TaskStatus.HUMAN_REQUIRED},
    TaskStatus.ROLLBACK_PENDING: {TaskStatus.ROLLING_BACK},
    TaskStatus.ROLLING_BACK:   {TaskStatus.READY, TaskStatus.HUMAN_REQUIRED},
    TaskStatus.HUMAN_REQUIRED: {TaskStatus.READY, TaskStatus.CANCELLED, TaskStatus.BLOCKED},
    TaskStatus.BLOCKED:        {TaskStatus.CANCELLED, TaskStatus.STALE},
    TaskStatus.STALE:          {TaskStatus.CANCELLED, TaskStatus.PENDING},
    TaskStatus.PASSED:         {TaskStatus.STALE},
    TaskStatus.CANCELLED:      set(),
}

# States that signal recovered/healthy — clear stale failure_reason.
_RECOVERY_STATES: set[TaskStatus] = {TaskStatus.PASSED, TaskStatus.READY}


class InvalidTransition(Exception):
    """Raised when a task attempts a disallowed state transition."""
    pass


def _resolve_transitions(status: TaskStatus) -> set[TaskStatus]:
    """Return the allowed transition set for *status*, failing loudly if unregistered."""
    try:
        return TRANSITIONS[status]
    except KeyError:
        raise RuntimeError(f"TaskStatus {status!r} has no TRANSITIONS entry — missing FSM registration")


def transition(task: Task, next_status: TaskStatus, reason: str = "") -> None:
    """Validate and apply a state transition.

    Records the destination in *status_history*.
    Sets *failure_reason* when transitioning to a failure state, and clears it
    on recovery transitions (PASSED / READY).
    """
    allowed = _resolve_transitions(task.status)
    if next_status not in allowed:
        raise InvalidTransition(
            f"{task.id}: {task.status.value} → {next_status.value}"
        )
    task.status = next_status
    task.status_history.append(next_status.value)

    if next_status in _RECOVERY_STATES:
        task.failure_reason = ""
    elif reason:
        task.failure_reason = reason


def can_transition(task: Task, next_status: TaskStatus) -> bool:
    """Return True if *task* can legally move to *next_status*."""
    return next_status in _resolve_transitions(task.status)
