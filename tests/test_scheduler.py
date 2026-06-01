from ai_runtime.task import Task, TaskStatus
from ai_runtime.graph import TaskGraph
from ai_runtime.scheduler import Scheduler


def test_next_ready_picks_first_satisfied():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", depends_on=["A"]))
    g.add(Task(id="C", type="design", depends_on=["A"]))
    s = Scheduler(g)
    t = s.next_ready()
    assert t is not None
    assert t.id in ("B", "C")


def test_next_ready_returns_none_when_blocked():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.FAILED))  # not PENDING
    g.add(Task(id="B", type="design", depends_on=["A"]))               # dep not PASSED
    s = Scheduler(g)
    assert s.next_ready() is None


def test_scheduler_is_done():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    s = Scheduler(g)
    assert s.is_done() is True


def test_scheduler_not_done():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PENDING))
    g.add(Task(id="B", type="design", status=TaskStatus.FAILED))
    s = Scheduler(g)
    assert s.is_done() is False


def test_dispatch_moves_through_ready_dispatched_running():
    g = TaskGraph()
    t = Task(id="A", type="requirement")
    g.add(t)
    Scheduler.dispatch(t)
    assert t.status == TaskStatus.RUNNING
    assert t.status_history == ["ready", "dispatched", "running"]


def test_mark_passed_transitions_correctly():
    t = Task(id="A", type="requirement", status=TaskStatus.RUNNING)
    Scheduler.mark_passed(t)
    assert t.status == TaskStatus.PASSED


def test_mark_failed_sets_reason():
    t = Task(id="A", type="requirement", status=TaskStatus.RUNNING)
    Scheduler.mark_failed(t, "something broke")
    assert t.status == TaskStatus.FAILED
    assert t.failure_reason == "something broke"


def test_mark_human_required_transitions():
    t = Task(id="A", type="requirement", status=TaskStatus.FAILED)
    Scheduler.mark_human_required(t, "need review")
    assert t.status == TaskStatus.HUMAN_REQUIRED
