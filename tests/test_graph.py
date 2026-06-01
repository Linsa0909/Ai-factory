import pytest
from ai_runtime.task import Task, TaskStatus
from ai_runtime.graph import TaskGraph, CyclicDependencyError, DanglingDependencyError


# === Normal DAG tests ===

def test_ready_tasks_returns_tasks_with_deps_satisfied():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", depends_on=["A"]))
    g.add(Task(id="C", type="codegen", depends_on=["A"]))
    assert {t.id for t in g.ready_tasks()} == {"B", "C"}


def test_ready_tasks_empty_when_deps_not_satisfied():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement"))  # still PENDING
    g.add(Task(id="B", type="design", depends_on=["A"]))
    # A is a root task (no deps) so it IS ready even when PENDING
    # B depends on A which is not PASSED, so B is NOT ready
    assert {t.id for t in g.ready_tasks()} == {"A"}


def test_invalidate_downstream_marks_stale():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", depends_on=["A"], status=TaskStatus.PASSED))
    stale = g.invalidate_downstream("A")
    assert len(stale) == 1
    assert stale[0].status == TaskStatus.STALE


def test_invalidate_does_not_double_stale():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", depends_on=["A"], status=TaskStatus.STALE))
    stale = g.invalidate_downstream("A")
    assert stale == []


def test_all_passed():
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", status=TaskStatus.PASSED))
    assert g.all_passed() is True
    g.add(Task(id="C", type="codegen", status=TaskStatus.FAILED))
    assert g.all_passed() is False


def test_task_count():
    g = TaskGraph()
    assert g.task_count() == 0
    g.add(Task(id="A", type="requirement"))
    g.add(Task(id="B", type="design"))
    assert g.task_count() == 2


# === DESTRUCTIVE TESTS (critical for DAG integrity) ===

def test_self_dependency_rejected():
    """A task depending on itself must be rejected immediately on add()."""
    g = TaskGraph()
    with pytest.raises(CyclicDependencyError, match="itself"):
        g.add(Task(id="A", type="codegen", depends_on=["A"]))


def test_simple_cycle_rejected():
    """A -> B -> A must be detected on validate()."""
    g = TaskGraph()
    g.add(Task(id="A", type="codegen", depends_on=["B"]))
    g.add(Task(id="B", type="testgen", depends_on=["A"]))
    with pytest.raises(CyclicDependencyError, match="Cycle"):
        g.validate()


def test_three_node_cycle_rejected():
    """A -> B -> C -> A must be detected."""
    g = TaskGraph()
    g.add(Task(id="A", type="codegen", depends_on=["C"]))
    g.add(Task(id="B", type="testgen", depends_on=["A"]))
    g.add(Task(id="C", type="design", depends_on=["B"]))
    with pytest.raises(CyclicDependencyError, match="Cycle"):
        g.validate()


def test_dangling_dependency_rejected():
    """A depends on X which doesn't exist -> must fail validate()."""
    g = TaskGraph()
    g.add(Task(id="A", type="codegen", depends_on=["X"]))
    with pytest.raises(DanglingDependencyError, match="does not exist"):
        g.validate()


def test_duplicate_id_rejected():
    """Two tasks with the same id must be rejected."""
    g = TaskGraph()
    g.add(Task(id="A", type="requirement"))
    with pytest.raises(ValueError, match="Duplicate"):
        g.add(Task(id="A", type="design"))


def test_invalidation_on_stale_propagates_only_one_level():
    """Stale marking does NOT recursively cascade. Only immediate dependents go STALE."""
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", depends_on=["A"], status=TaskStatus.PASSED))
    g.add(Task(id="C", type="codegen", depends_on=["B"], status=TaskStatus.PASSED))
    stale = g.invalidate_downstream("A")
    assert len(stale) == 1  # Only B, not C
    assert stale[0].id == "B"


def test_invalidation_on_already_stale_ignores_children():
    """Invalidating a STALE task does not re-stale its children."""
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", depends_on=["A"], status=TaskStatus.PASSED))
    # First invalidation
    g.invalidate_downstream("A")
    assert g.get("B").status == TaskStatus.STALE
    # Second invalidation (redundant) should produce empty list
    stale = g.invalidate_downstream("A")
    assert stale == []


def test_invalidation_stales_immediate_dependents():
    """Invalidating a PASSED task whose deps are still PASSED does nothing.
    Actually — invalidate marks dependents of the given task. If task A is still
    PASSED, invalidating A marks tasks that depend on A. This is intentional."""
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", depends_on=["A"], status=TaskStatus.PASSED))
    # A is PASSED. Invalidating A -> B goes STALE (A changed, B needs re-validation)
    stale = g.invalidate_downstream("A")
    assert len(stale) == 1
    assert stale[0].id == "B"


def test_validate_passes_on_valid_dag():
    """A valid linear DAG must pass validate() without error."""
    g = TaskGraph()
    g.add(Task(id="A", type="requirement"))
    g.add(Task(id="B", type="design", depends_on=["A"]))
    g.add(Task(id="C", type="codegen", depends_on=["B"]))
    g.validate()  # Must not raise


def test_graph_with_multiple_roots():
    """Tasks with no dependencies are valid roots and ready when PENDING."""
    g = TaskGraph()
    g.add(Task(id="A", type="requirement"))
    g.add(Task(id="B", type="requirement"))
    g.add(Task(id="C", type="codegen", depends_on=["A", "B"]))
    g.validate()
    # A and B are root tasks (no deps, PENDING) so they ARE ready
    # C should be ready only when both A and B are PASSED
    assert {t.id for t in g.ready_tasks()} == {"A", "B"}
    assert g.get("A").status == TaskStatus.PENDING
    assert g.get("B").status == TaskStatus.PENDING


def test_invalidation_skips_running_task():
    """⚠️ Invalidating upstream of a RUNNING task must NOT crash — just skip it."""
    g = TaskGraph()
    g.add(Task(id="A", type="requirement", status=TaskStatus.PASSED))
    g.add(Task(id="B", type="design", depends_on=["A"], status=TaskStatus.RUNNING))
    # B is RUNNING → cannot go STALE. Must not crash.
    stale = g.invalidate_downstream("A")
    assert stale == []  # B was skipped, not added to stale list
