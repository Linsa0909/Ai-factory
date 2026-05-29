from ai_runtime.task import Task, TaskStatus


def test_task_default_status_is_pending():
    t = Task(id="T1", type="codegen")
    assert t.status == TaskStatus.PENDING


def test_task_to_dict_and_back():
    t = Task(id="DEV-TODO", type="codegen", module="todo", depends_on=["TEST-TODO"])
    d = t.to_dict()
    t2 = Task.from_dict(d)
    assert t2.id == "DEV-TODO"
    assert t2.status == TaskStatus.PENDING
    assert t2.depends_on == ["TEST-TODO"]


def test_task_status_is_string_enum():
    assert TaskStatus.PASSED.value == "passed"
    assert TaskStatus.FAILED.value == "failed"
    assert TaskStatus.WAITING_RETRY.value == "waiting_retry"
    assert TaskStatus.STALE.value == "stale"
