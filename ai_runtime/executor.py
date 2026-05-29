"""Execution runner for dev tools. P0: pytest, ruff, mypy."""

import asyncio
from dataclasses import dataclass


@dataclass
class ExecResult:
    success: bool
    command: str
    stdout: str
    stderr: str
    exit_code: int


class ExecutionRunner:
    """Run pytest, ruff, mypy in subprocesses with timeouts."""

    def __init__(self, workspace: str) -> None:
        self.workspace = workspace

    async def _run(self, *args: str, timeout: int = 120) -> ExecResult:
        cmd = list(args)
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=self.workspace,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return ExecResult(
                success=False, command=" ".join(cmd),
                stdout="", stderr=f"Timeout after {timeout}s", exit_code=-1,
            )
        return ExecResult(
            success=proc.returncode == 0, command=" ".join(cmd),
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else "",
            exit_code=proc.returncode or 0,
        )

    async def run_pytest(self) -> ExecResult:
        return await self._run(
            "python", "-m", "pytest", "tests/",
            "--ignore=tests/test_executor.py",
            "-v", "--tb=short",
        )

    async def run_ruff(self) -> ExecResult:
        return await self._run("ruff", "check", ".")

    async def run_mypy(self) -> ExecResult:
        return await self._run("mypy", ".", "--ignore-missing-imports")
