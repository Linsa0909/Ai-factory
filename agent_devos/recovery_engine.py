"""Recovery Engine — FixLoop + RetryPolicy + Hallucination Detection + Escalation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import sys
sys.path.insert(0, "/mnt/c/Users/Linsa/ai-factory-runtime")
from ai_runtime.task import Task
from ai_runtime.agent_adapter import AgentResult
from ai_runtime.fix_loop import AutoFixLoop, FixLoopConvergence

from agent_devos.execution_snapshot import ExecutionSnapshot


class RecoveryAction(str, Enum):
    RETRY = "retry"
    ESCALATE = "escalate"
    IGNORE = "ignore"


@dataclass
class RecoveryResult:
    action: RecoveryAction
    reason: str
    fixed: bool = False


@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_seconds: list[int] = field(default_factory=lambda: [10, 30, 60])

    def should_retry(self, task: Task) -> bool:
        return task.retry_count < self.max_retries

    def detect_hallucination(
        self, result: AgentResult, task: Task, prev_output: str = ""
    ) -> bool:
        """Detect hallucination signals in agent output.
        Signals: repeated output, entropy rising (>2x), claimed fix but no content.
        """
        if prev_output and result.output.strip() == prev_output.strip():
            return True
        if prev_output and len(result.output) > len(prev_output) * 2:
            return True
        if "fixed" in result.output.lower() and len(result.output) < 100:
            return True
        return False


class RecoveryEngine:
    """Orchestrates failure recovery: retry -> FixLoop -> hallucination check -> escalate."""

    def __init__(self, fix_loop: AutoFixLoop, policy: RetryPolicy | None = None) -> None:
        self.fix_loop = fix_loop
        self.policy = policy or RetryPolicy()

    async def handle_failure(
        self,
        task: Task,
        result: AgentResult,
        snapshot: ExecutionSnapshot,
        workspace: str,
    ) -> RecoveryResult:
        # 1. Check if retryable
        if not self.policy.should_retry(task):
            return RecoveryResult(
                action=RecoveryAction.ESCALATE,
                reason=f"max_retries ({self.policy.max_retries}) exceeded",
            )

        # 2. Check hallucination
        if self.policy.detect_hallucination(result, task, task.failure_reason):
            return RecoveryResult(
                action=RecoveryAction.ESCALATE,
                reason="hallucination_detected: output repeating or entropy rising",
            )

        # 3. Attempt FixLoop
        try:
            fix_result = await self.fix_loop.run(task, workspace)
            return RecoveryResult(
                action=RecoveryAction.RETRY,
                reason=f"fix_loop: {fix_result}",
                fixed=True,
            )
        except FixLoopConvergence as e:
            return RecoveryResult(
                action=RecoveryAction.ESCALATE,
                reason=f"fix_loop_non_convergent: {e}",
            )
