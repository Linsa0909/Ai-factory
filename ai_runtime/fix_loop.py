"""Fix loop: orchestrates auto-fix flow. Delegates to convergence, scope, executor, adapter."""

from ai_runtime.task import Task, TaskStatus
from ai_runtime.fsm import transition
from ai_runtime.agent_adapter import AgentAdapter, AgentResult
from ai_runtime.executor import ExecutionRunner
from ai_runtime.convergence import check_convergence, error_signature, ConvergenceError
from ai_runtime.scope import validate_patch_scope
from ai_runtime.policy import SCOPE_ALLOWED, SCOPE_FORBIDDEN


FIX_PROMPT = """You are fixing test failures in a Python project.

Rules:
1. Only modify files in the target module
2. Do NOT modify the test files
3. Make minimal changes
4. Fix ONLY the failing tests
5. Do not add features or change function signatures

Output each changed file with this exact format:
```python:backend/app/{module}/file.py
...complete file content...
```
Do NOT use unified diffs. Output the COMPLETE file content."""


class FixLoopConvergence(Exception):
    """Raised when auto-fix loop cannot converge and must escalate to human."""
    pass


class AutoFixLoop:
    """Handle pytest failure -> fix -> retry -> converge or escalate to human."""

    def __init__(self, adapter: AgentAdapter, runner: ExecutionRunner) -> None:
        self.adapter = adapter
        self.runner = runner

    async def run(self, task: Task, workspace: str) -> str:
        """
        Run auto-fix loop. Returns "resolved" or raises FixLoopConvergence.

        Each iteration:
        1. Run pytest -> if pass, return "resolved"
        2. Check convergence -> if fail, raise FixLoopConvergence
        3. Send failure to agent -> get fix
        4. Check scope of changes (if files_changed populated)
        """
        prev_error = ""
        prev_size = 0

        for iteration in range(1, task.max_retry + 1):
            # Step 1: Run pytest
            result = await self.runner.run_pytest()
            if result.success:
                return "resolved"

            curr_error = error_signature(result.stdout)
            curr_size = len(result.stdout)

            # Step 2: Check convergence
            try:
                check_convergence(
                    retry_count=iteration,
                    current_error=curr_error,
                    previous_error=prev_error,
                    previous_output_size=prev_size,
                    current_output_size=curr_size,
                )
            except ConvergenceError as e:
                raise FixLoopConvergence(str(e))

            prev_error = curr_error
            prev_size = curr_size

            # Step 3: Transition to FIXING
            # If task is in VERIFYING from a prior attempt, route through
            # FAILED -> WAITING_RETRY per the FSM.
            if task.status == TaskStatus.VERIFYING:
                transition(task, TaskStatus.FAILED)
                transition(task, TaskStatus.WAITING_RETRY)
            transition(task, TaskStatus.FIXING)
            agent_result = await self._attempt_fix(task, result.stdout, workspace)

            if not agent_result.success:
                raise FixLoopConvergence(
                    f"Fix agent failed: {agent_result.output[:200]}"
                )

            # Step 4: Scope check (if files were changed)
            if agent_result.files_changed:
                patterns = [p.format(module=task.module) for p in SCOPE_ALLOWED.get("fix", SCOPE_ALLOWED["fix"])]
                ok, violations = validate_patch_scope(
                    agent_result.files_changed, patterns, SCOPE_FORBIDDEN, workspace,
                )
                if not ok:
                    raise FixLoopConvergence(f"Scope violation: {violations}")

            transition(task, TaskStatus.VERIFYING)
            task.retry_count = iteration

        raise FixLoopConvergence(f"Max retries ({task.max_retry}) exceeded")

    async def _attempt_fix(self, task: Task, test_output: str, workspace: str) -> AgentResult:
        """Send test failure to agent and get a fix."""
        context = (
            f"## Test Failure Output\n\n```\n{test_output}\n```\n\n"
            f"## Module\n{task.module}"
        )
        return await self.adapter.run("dev", FIX_PROMPT, context, workspace)
