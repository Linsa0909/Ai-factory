from ai_runtime.task import Task, TaskStatus

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
    TaskStatus.PASSED:         set(),
    TaskStatus.CANCELLED:      set(),
}


class InvalidTransition(Exception):
    pass


def transition(task: Task, next_status: TaskStatus, reason: str = "") -> None:
    if next_status not in TRANSITIONS.get(task.status, set()):
        raise InvalidTransition(
            f"{task.id}: {task.status.value} → {next_status.value}"
        )
    task.status = next_status
    task.status_history.append(next_status.value)
    if reason:
        task.failure_reason = reason


def can_transition(task: Task, next_status: TaskStatus) -> bool:
    return next_status in TRANSITIONS.get(task.status, set())
