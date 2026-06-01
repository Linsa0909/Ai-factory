import pytest
from unittest.mock import AsyncMock, MagicMock
from ai_runtime.fix_loop import AutoFixLoop, FixLoopConvergence, FIX_PROMPT
from ai_runtime.task import Task, TaskStatus
from ai_runtime.agent_adapter import AgentResult
from ai_runtime.executor import ExecResult


async def test_fix_loop_resolves_when_pytest_passes_immediately():
    """First pytest run passes -> return "resolved" without any fix attempt."""
    mock_adapter = MagicMock()
    mock_runner = MagicMock()
    mock_runner.run_pytest = AsyncMock(return_value=ExecResult(
        success=True, command="pytest", stdout="all passed", stderr="", exit_code=0,
    ))

    loop = AutoFixLoop(mock_adapter, mock_runner)
    task = Task(id="FIX-TEST", type="verify", module="todo", max_retry=3)

    result = await loop.run(task, "/tmp/workspace")
    assert result == "resolved"
    mock_adapter.run.assert_not_called()  # No fix needed


async def test_fix_loop_raises_on_max_retries():
    """After max_retry failures, must raise FixLoopConvergence."""
    mock_adapter = MagicMock()
    mock_runner = MagicMock()

    call_count = 0

    async def diff_errors():
        nonlocal call_count
        call_count += 1
        return ExecResult(
            success=False, command="pytest",
            stdout=f"FAILED test_{call_count}\nERROR test_{call_count}\nE   assert {call_count} == 0",
            stderr="", exit_code=1,
        )

    mock_runner.run_pytest = AsyncMock(side_effect=diff_errors)
    mock_adapter.run = AsyncMock(return_value=AgentResult(
        success=True, output="mock fix", files_changed=[], tokens_used=10, model="deepseek",
    ))

    loop = AutoFixLoop(mock_adapter, mock_runner)
    task = Task(id="FIX-TEST", type="verify", module="todo", max_retry=2, status=TaskStatus.WAITING_RETRY)

    with pytest.raises(FixLoopConvergence, match="Max retries"):
        await loop.run(task, "/tmp/workspace")

    assert mock_runner.run_pytest.call_count == 2


async def test_fix_loop_raises_on_same_error_repeated():
    """Same error twice -> convergence check stops it."""
    mock_adapter = MagicMock()
    mock_runner = MagicMock()

    # Always return the same failure
    mock_runner.run_pytest = AsyncMock(return_value=ExecResult(
        success=False, command="pytest",
        stdout="FAILED test_a\nERROR test_a\nE   assert 1 == 2",
        stderr="", exit_code=1,
    ))
    mock_adapter.run = AsyncMock(return_value=AgentResult(
        success=True, output="try fix", files_changed=[], tokens_used=10, model="deepseek",
    ))

    loop = AutoFixLoop(mock_adapter, mock_runner)
    task = Task(id="FIX-TEST", type="verify", module="todo", max_retry=3, status=TaskStatus.WAITING_RETRY)

    with pytest.raises(FixLoopConvergence, match="Same error"):
        await loop.run(task, "/tmp/workspace")

    # Second call should trigger same-error detection
    assert mock_runner.run_pytest.call_count == 2


async def test_fix_loop_raises_when_agent_fails():
    """Agent returns failure -> escalate immediately."""
    mock_adapter = MagicMock()
    mock_runner = MagicMock()
    mock_runner.run_pytest = AsyncMock(return_value=ExecResult(
        success=False, command="pytest", stdout="FAILED test_a\n",
        stderr="", exit_code=1,
    ))
    mock_adapter.run = AsyncMock(return_value=AgentResult(
        success=False, output="API rate limit exceeded",
        files_changed=[], tokens_used=0, model="deepseek",
    ))

    loop = AutoFixLoop(mock_adapter, mock_runner)
    task = Task(id="FIX-TEST", type="verify", module="todo", max_retry=3, status=TaskStatus.WAITING_RETRY)

    with pytest.raises(FixLoopConvergence, match="Fix agent failed"):
        await loop.run(task, "/tmp/workspace")


async def test_fix_loop_raises_on_scope_violation():
    """Agent changes a forbidden file -> scope check catches it."""
    mock_adapter = MagicMock()
    mock_runner = MagicMock()
    mock_runner.run_pytest = AsyncMock(return_value=ExecResult(
        success=False, command="pytest", stdout="FAILED test_a\n",
        stderr="", exit_code=1,
    ))
    mock_adapter.run = AsyncMock(return_value=AgentResult(
        success=True, output="fixed",
        files_changed=["backend/app/core/db.py"],  # FORBIDDEN
        tokens_used=10, model="deepseek",
    ))

    loop = AutoFixLoop(mock_adapter, mock_runner)
    task = Task(id="FIX-TEST", type="verify", module="todo", max_retry=3, status=TaskStatus.WAITING_RETRY)

    with pytest.raises(FixLoopConvergence, match="Scope violation"):
        await loop.run(task, "/tmp/workspace")


async def test_fix_loop_retry_count_increments():
    """task.retry_count must increment on each fix attempt."""
    mock_adapter = MagicMock()
    mock_runner = MagicMock()

    call_count = 0

    async def eventually_pass():
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            return ExecResult(success=True, command="pytest", stdout="passed", stderr="", exit_code=0)
        return ExecResult(success=False, command="pytest",
                          stdout=f"FAILED test_{call_count}\nERROR test_{call_count}\nE   assert {call_count} == 0",
                          stderr="", exit_code=1)

    mock_runner.run_pytest = AsyncMock(side_effect=eventually_pass)
    mock_adapter.run = AsyncMock(return_value=AgentResult(
        success=True, output="fix", files_changed=[], tokens_used=10, model="deepseek",
    ))

    loop = AutoFixLoop(mock_adapter, mock_runner)
    task = Task(id="FIX-TEST", type="verify", module="todo", max_retry=3, status=TaskStatus.WAITING_RETRY)

    result = await loop.run(task, "/tmp/workspace")
    assert result == "resolved"
    assert task.retry_count == 2  # fixes happened in iterations 1 and 2, pass on 3


async def test_fix_prompt_contains_rules():
    """FIX_PROMPT must include key constraint phrases."""
    assert "minimal changes" in FIX_PROMPT.lower()
    assert "do not modify the test files" in FIX_PROMPT.lower()
    assert "complete file content" in FIX_PROMPT.lower()
