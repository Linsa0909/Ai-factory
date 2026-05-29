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


def test_to_dict_from_dict_full_roundtrip():
    """Verify all fields survive a serialize/deserialize cycle."""
    t = Task(
        id="FULL", type="codegen", module="todo",
        depends_on=["A", "B"],
        retry_count=2, max_retry=5,
        timeout_seconds=900, model="claude",
        status_history=["pending", "ready"],
        failure_reason="something broke",
        snapshot_before="abc123", snapshot_after="def456",
        outputs=["file1.py"],
    )
    d = t.to_dict()
    t2 = Task.from_dict(d)
    assert t2.id == "FULL"
    assert t2.type == "codegen"
    assert t2.module == "todo"
    assert t2.depends_on == ["A", "B"]
    assert t2.retry_count == 2
    assert t2.max_retry == 5
    assert t2.timeout_seconds == 900
    assert t2.model == "claude"
    assert t2.status_history == ["pending", "ready"]
    assert t2.failure_reason == "something broke"
    assert t2.snapshot_before == "abc123"
    assert t2.snapshot_after == "def456"
    assert t2.outputs == ["file1.py"]


def test_task_status_is_string_enum():
    assert TaskStatus.PASSED.value == "passed"
    assert TaskStatus.FAILED.value == "failed"
    assert TaskStatus.WAITING_RETRY.value == "waiting_retry"
    assert TaskStatus.STALE.value == "stale"
