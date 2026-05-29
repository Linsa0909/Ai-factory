from pathlib import Path

from ai_runtime.executor import ExecutionRunner, ExecResult

PROJECT_ROOT = Path(__file__).parent.parent


async def test_exec_result_defaults():
    r = ExecResult(success=True, command="pytest", stdout="OK", stderr="", exit_code=0)
    assert r.success is True
    assert r.command == "pytest"
    assert r.exit_code == 0


def test_runner_accepts_workspace():
    runner = ExecutionRunner("/tmp")
    assert runner.workspace == "/tmp"


async def test_run_pytest_executes():
    """Real subprocess test — runs pytest on the ai-runtime project itself.

    `run_pytest` ignores `test_executor.py` to prevent recursive subprocess
    spawning during testing. ruff/mypy scan full project — this is intentional.
    """
    runner = ExecutionRunner(str(PROJECT_ROOT))
    result = await runner.run_pytest()
    assert result.success is True, f"pytest should pass, got: {result.stderr}"


async def test_run_ruff_executes():
    """Real subprocess test — runs ruff check on the project."""
    runner = ExecutionRunner(str(PROJECT_ROOT))
    result = await runner.run_ruff()
    assert result.success is True, f"ruff should pass, got: {result.stderr}"


async def test_run_mypy_executes():
    """Real subprocess test — runs mypy on the project."""
    runner = ExecutionRunner(str(PROJECT_ROOT))
    result = await runner.run_mypy()
    assert result.success is True, f"mypy should pass, got: {result.stderr}"
