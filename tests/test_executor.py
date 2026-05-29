import asyncio
from ai_runtime.executor import ExecutionRunner, ExecResult


async def test_exec_result_defaults():
    r = ExecResult(success=True, command="pytest", stdout="OK", stderr="", exit_code=0)
    assert r.success is True
    assert r.command == "pytest"
    assert r.exit_code == 0


def test_runner_accepts_workspace():
    runner = ExecutionRunner("/tmp")
    assert runner.workspace == "/tmp"


async def test_run_pytest_executes():
    """⚠️ Real subprocess test — runs pytest on the ai-runtime project itself."""
    runner = ExecutionRunner("/mnt/c/Users/Linsa/ai-factory-runtime")
    result = await runner.run_pytest()
    assert result.success is True, f"pytest should pass, got: {result.stderr}"
