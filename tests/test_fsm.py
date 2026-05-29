import pytest
from ai_runtime.task import Task, TaskStatus
from ai_runtime.fsm import transition, InvalidTransition, can_transition


# === Normal transition tests ===

def test_pending_to_ready_valid():
    t = Task(id="T1", type="codegen")
    transition(t, TaskStatus.READY)
    assert t.status == TaskStatus.READY


def test_pending_to_passed_invalid():
    t = Task(id="T1", type="codegen")
    with pytest.raises(InvalidTransition):
        transition(t, TaskStatus.PASSED)


def test_passed_is_terminal():
    t = Task(id="T1", type="codegen", status=TaskStatus.PASSED)
    assert not can_transition(t, TaskStatus.RUNNING)
    assert not can_transition(t, TaskStatus.CANCELLED)


def test_full_verify_loop():
    """Simulate: RUNNING -> FAILED -> WAITING_RETRY -> FIXING -> VERIFYING -> PASSED"""
    t = Task(id="T1", type="verify", status=TaskStatus.RUNNING)
    transition(t, TaskStatus.FAILED, reason="pytest_failed")
    transition(t, TaskStatus.WAITING_RETRY)
    transition(t, TaskStatus.FIXING)
    transition(t, TaskStatus.VERIFYING)
    transition(t, TaskStatus.PASSED)
    assert t.status == TaskStatus.PASSED
    assert len(t.status_history) == 5


def test_stale_can_go_back_to_pending():
    t = Task(id="T1", type="codegen", status=TaskStatus.STALE)
    transition(t, TaskStatus.PENDING)
    assert t.status == TaskStatus.PENDING


# === DESTRUCTIVE TESTS (critical for state consistency) ===

def test_cannot_transition_from_terminal_passed():
    """PASSED has only one exit transition: -> STALE (cache invalidation)."""
    t = Task(id="T1", type="codegen", status=TaskStatus.PASSED)
    for bad_status in TaskStatus:
        if bad_status == TaskStatus.STALE:
            continue  # STALE is the sole valid exit (DAG invalidation)
        assert not can_transition(t, bad_status), f"PASSED -> {bad_status.value} must be rejected"


def test_cannot_transition_from_terminal_cancelled():
    """CANCELLED is terminal. No exit transitions allowed."""
    t = Task(id="T1", type="codegen", status=TaskStatus.CANCELLED)
    for bad_status in TaskStatus:
        assert not can_transition(t, bad_status), f"CANCELLED -> {bad_status.value} must be rejected"


def test_cannot_re_run_passed_task():
    """RUNNING -> PASSED -> try to transition again -> must fail."""
    t = Task(id="T1", type="codegen", status=TaskStatus.RUNNING)
    transition(t, TaskStatus.PASSED)
    with pytest.raises(InvalidTransition):
        transition(t, TaskStatus.RUNNING)  # Can't re-run a passed task


def test_cannot_skip_states_in_fix_chain():
    """FAILED -> FIXING directly is illegal (must be FAILED -> WAITING_RETRY -> FIXING -> VERIFYING)."""
    t = Task(id="T1", type="codegen", status=TaskStatus.FAILED)
    with pytest.raises(InvalidTransition):
        transition(t, TaskStatus.FIXING)  # Must go through WAITING_RETRY first


def test_cannot_go_backwards_in_normal_flow():
    """RUNNING -> PASSED is the forward path. PASSED -> RUNNING is backwards and illegal."""
    t = Task(id="T1", type="codegen", status=TaskStatus.RUNNING)
    transition(t, TaskStatus.PASSED)
    # Now at PASSED (terminal), backtracking to RUNNING must fail
    with pytest.raises(InvalidTransition):
        transition(t, TaskStatus.RUNNING)


def test_direct_status_mutation_leaves_history_inconsistent():
    """Demonstrate that bypassing transition() corrupts state history.
    This test exists to document the risk - the FSM cannot prevent direct
    attribute mutation in Python, but consumers MUST use transition()."""
    t = Task(id="T1", type="codegen", status=TaskStatus.RUNNING)
    # BAD: direct mutation bypasses transition()
    t.status = TaskStatus.PASSED
    assert t.status == TaskStatus.PASSED
    assert t.status_history == []  # History NOT recorded - this is the corruption
    # This test serves as a warning: always use transition(), never direct assignment.


def test_transition_records_history_correctly():
    """Verify history records exact sequence after every valid transition."""
    t = Task(id="T1", type="codegen")
    transition(t, TaskStatus.READY)
    transition(t, TaskStatus.DISPATCHED)
    transition(t, TaskStatus.RUNNING)
    assert t.status_history == ["ready", "dispatched", "running"]


def test_transition_sets_failure_reason():
    """Failure reason must be set atomically with the transition."""
    t = Task(id="T1", type="codegen", status=TaskStatus.RUNNING)
    reason = "connection refused to database:5432"
    transition(t, TaskStatus.FAILED, reason=reason)
    assert t.status == TaskStatus.FAILED
    assert t.failure_reason == reason


def test_invalid_transition_does_not_mutate():
    """A failed transition must leave task state completely unchanged."""
    t = Task(id="T1", type="codegen")
    original_status = t.status
    original_history = list(t.status_history)
    original_reason = t.failure_reason
    try:
        transition(t, TaskStatus.PASSED)  # PENDING -> PASSED is illegal
    except InvalidTransition:
        pass
    assert t.status == original_status
    assert t.status_history == original_history
    assert t.failure_reason == original_reason


def test_failure_reason_cleared_on_recovery():
    """⚠️ FAILED → ... → PASSED must clear stale failure_reason."""
    t = Task(id="T1", type="verify", status=TaskStatus.RUNNING)
    transition(t, TaskStatus.FAILED, reason="db timeout")
    assert t.failure_reason == "db timeout"
    transition(t, TaskStatus.WAITING_RETRY)
    transition(t, TaskStatus.FIXING)
    transition(t, TaskStatus.VERIFYING)
    transition(t, TaskStatus.PASSED)
    assert t.status == TaskStatus.PASSED
    assert t.failure_reason == "", f"failure_reason should be cleared on PASSED, got: {t.failure_reason}"


def test_unregistered_status_fails_loudly():
    """⚠️ If a TaskStatus is missing from TRANSITIONS, fail with RuntimeError, not silent."""
    from unittest.mock import MagicMock
    t = MagicMock(spec=Task)
    t.status = "not-a-real-status"
    with pytest.raises(RuntimeError, match="no TRANSITIONS entry"):
        can_transition(t, TaskStatus.PASSED)
