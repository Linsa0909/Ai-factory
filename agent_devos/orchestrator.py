"""Orchestrator — top-level facade that wires all AgentDevOS layers together.

This is the single entry point. It:
  1. Loads agent.md files -> AgentSpecs
  2. Builds DAG via DAGBuilder
  3. Creates Scheduler with TaskMeta
  4. Creates ArtifactRegistry, GlobalPolicyEngine, RecoveryEngine
  5. Exposes run_once() for step-by-step execution
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json

# Import ai-runtime (read-only base)
import sys
sys.path.insert(0, "/mnt/c/Users/Linsa/ai-factory-runtime")
from ai_runtime.task import Task, TaskStatus
from ai_runtime.graph import TaskGraph
from ai_runtime.fsm import transition
from ai_runtime.agent_adapter import AgentAdapter, AgentResult
from ai_runtime.snapshot import SnapshotManager
from ai_runtime.executor import ExecutionRunner
from ai_runtime.fix_loop import AutoFixLoop
from ai_runtime.patch_engine import PatchEngine

# Import AgentDevOS layers
from agent_devos.agent_loader import AgentLoader, AgentSpec
from agent_devos.artifact_registry import ArtifactRegistry, ArtifactEntry
from agent_devos.global_policy import GlobalPolicyEngine
from agent_devos.dag_builder import DAGBuilder, TaskMeta
from agent_devos.scheduler import Scheduler
from agent_devos.context_assembler import ContextAssembler
from agent_devos.execution_snapshot import ExecutionSnapshot
from agent_devos.tool_registry import ToolRegistry
from agent_devos.recovery_engine import RecoveryEngine, RetryPolicy
from agent_devos.human_gate import HumanGate, GateDecision


class Orchestrator:
    """Top-level facade for AgentDevOS multi-agent pipeline."""

    def __init__(
        self,
        workspace: str,
        agents_dir: str,
        deepseek_api_key: str = "",
        profile: str = "",
    ) -> None:
        self.workspace = Path(workspace)
        self.agents_dir = Path(agents_dir)

        # Layer 1: Agent specs
        self.specs: list[AgentSpec] = []
        self.spec_map: dict[str, AgentSpec] = {}

        # Layer 2: Artifact & Policy
        self.registry = ArtifactRegistry()
        self.policy = GlobalPolicyEngine()
        self.dag_builder = DAGBuilder()

        # Layer 3: Graph & Scheduler
        self.graph: TaskGraph | None = None
        self.metas: dict[str, TaskMeta] = {}
        self.scheduler: Scheduler | None = None

        # Layer 4: Runtime bridge
        self.adapter = AgentAdapter(deepseek_api_key=deepseek_api_key)
        self.snapshots = SnapshotManager(workspace)
        self.executor = ExecutionRunner(workspace)
        self.patcher = PatchEngine(workspace)
        self.fix_loop = AutoFixLoop(self.adapter, self.executor)

        # Layer 5: Context & Recovery
        self.context_assembler = ContextAssembler()
        self.recovery = RecoveryEngine(self.fix_loop, RetryPolicy())

        # Layer 6: Human gate
        self.human_gate = HumanGate()

        # State
        self._profile = profile
        self._snapshots: dict[str, ExecutionSnapshot] = {}

    # ---- Initialization ----

    def load_agents(self) -> list[AgentSpec]:
        """Load all agent.md files and build the execution DAG."""
        self.specs = AgentLoader.load_all(str(self.agents_dir))
        self.spec_map = {s.id: s for s in self.specs}
        self.graph, self.metas = self.dag_builder.build(
            self.specs, self.registry, self.policy
        )
        self.scheduler = Scheduler(self.graph, self.metas)

        # Transition root tasks (no dependencies) from PENDING to READY
        for task in self.graph.all_tasks():
            if not task.depends_on:
                transition(task, TaskStatus.READY)

        # Catch up FSM from workspace files (state persistence via filesystem)
        self.catchup_from_workspace()

        return self.specs

    def catchup_from_workspace(self) -> None:
        """Catch up FSM states from .agentdevos/status.json.
        Reads status records written by Orchestrator — does NOT parse agent outputs.
        """
        status_path = self.workspace / ".agentdevos" / "status.json"
        if not status_path.exists():
            return

        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            return

        agents_status = data.get("agents", {})
        for agent_id, record in agents_status.items():
            task = self.graph.get(agent_id) if self.graph else None
            if task is None:
                continue
            if record.get("status") == "completed":
                self._advance_to_passed(task)

        # Cascade: make ready any task whose deps are all PASSED
        for task in self.graph.all_tasks():
            if task.status.value != "pending":
                continue
            if not task.depends_on:
                continue
            if all(
                self.graph.get(d) and self.graph.get(d).status.value == "passed"
                for d in task.depends_on
            ):
                try:
                    transition(task, TaskStatus.READY)
                except Exception:
                    pass

    def _verify_outputs(self, spec: AgentSpec) -> tuple[bool, list[str]]:
        """Verify agent outputs exist. Returns (all_exist, [missing_paths])."""
        missing = []
        for out_path in spec.outputs:
            clean = out_path.replace("{issue_id}/", "")
            fp = self.workspace / clean
            if "*" in clean:
                matches = list(self.workspace.glob(clean))
                if not matches:
                    missing.append(clean)
            elif not fp.exists():
                missing.append(clean)
        return len(missing) == 0, missing

    def _write_status(self, agent_id: str, status: str, outputs: list[str],
                      error: str = "", retry_count: int = 0) -> None:
        """Write agent status record to .agentdevos/status.json.
        Agent produces content; Orchestrator verifies and records.
        """
        status_dir = self.workspace / ".agentdevos"
        status_dir.mkdir(parents=True, exist_ok=True)
        status_path = status_dir / "status.json"

        data = {}
        if status_path.exists():
            try:
                data = json.loads(status_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        data.setdefault("agents", {})
        data["agents"][agent_id] = {
            "agent": agent_id,
            "status": status,
            "outputs": outputs,
            "error": error,
            "retry_count": retry_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        data.setdefault("pipeline", {})
        data["pipeline"]["last_updated"] = datetime.now(timezone.utc).isoformat()

        status_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _advance_to_passed(self, task: Task) -> None:
        """Advance a task from its current state to PASSED through valid FSM path."""
        s = task.status.value
        try:
            if s == "pending":
                transition(task, TaskStatus.READY)
                transition(task, TaskStatus.DISPATCHED)
                transition(task, TaskStatus.RUNNING)
                transition(task, TaskStatus.PASSED)
            elif s == "ready":
                transition(task, TaskStatus.DISPATCHED)
                transition(task, TaskStatus.RUNNING)
                transition(task, TaskStatus.PASSED)
            elif s == "dispatched":
                transition(task, TaskStatus.RUNNING)
                transition(task, TaskStatus.PASSED)
            elif s == "running":
                transition(task, TaskStatus.PASSED)
        except Exception:
            pass

    # ---- Execution ----

    async def run_once(self) -> str:
        """Execute one ready task (atomic). Returns 'done', 'blocked', or 'running'."""
        if self.scheduler is None:
            raise RuntimeError("No scheduler — call load_agents() first")

        task, meta = self.scheduler.next_ready()
        if task is None:
            return "done" if self.scheduler.is_done() else "blocked"

        spec = self.spec_map.get(task.id)
        if spec is None:
            raise RuntimeError(f"No AgentSpec for task '{task.id}'")

        # Atomic execution boundary
        states = {t.id: t.status.value for t in self.graph.all_tasks()}
        snap_id = self.snapshots.create(task.id, "before_run", states)

        exec_snap = ExecutionSnapshot.create(
            task_id=task.id,
            agent_md=spec.raw_md,
            upstream_artifacts=self._read_artifacts(meta),
            fsm_state=states,
            prompt_template=self._get_prompt(spec),
            model=task.model,
        )
        self._snapshots[task.id] = exec_snap

        try:
            self.scheduler.dispatch(task)
            self.scheduler.mark_running(task)

            context = self.context_assembler.build(
                spec, meta,
                fsm_states=states,
                workspace=str(self.workspace),
            )
            prompt = self._get_prompt(spec)

            result: AgentResult = await self.adapter.run(
                task.type, prompt, context, str(self.workspace)
            )

            if result.success:
                # Step 1: Agent produces — extract code or save raw output
                produced_files: list[str] = []
                try:
                    produced_files = self.patcher.extract_and_apply(result.output)
                except Exception:
                    out_file = self.workspace / f"{task.id}_output.md"
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(result.output, encoding="utf-8")
                    produced_files = [str(out_file.relative_to(self.workspace))]
                    import subprocess
                    subprocess.run(["git", "add", str(out_file.relative_to(self.workspace))],
                                   cwd=str(self.workspace), capture_output=True)

                # Step 2: Orchestrator verifies
                all_exist, missing = self._verify_outputs(spec)
                if not all_exist:
                    # Some outputs still missing — agent must retry
                    raise Exception(f"Output verification failed. Missing: {missing}")

                # Step 3: Orchestrator records
                self._write_status(
                    agent_id=task.id,
                    status="completed",
                    outputs=produced_files or spec.outputs,
                    retry_count=task.retry_count,
                )

                exec_snap.result_hash = ExecutionSnapshot.compute_hash(result.output)
                self.scheduler.mark_passed(task)

                # Step 4: Route — cascade downstream
                for t in self.graph.all_tasks():
                    if t.status.value != "pending":
                        continue
                    if not t.depends_on:
                        continue
                    if all(
                        self.graph.get(d) and self.graph.get(d).status.value == "passed"
                        for d in t.depends_on
                    ):
                        try:
                            transition(t, TaskStatus.READY)
                        except Exception:
                            pass

                return "running"
            else:
                self._write_status(task.id, "failed", [], error=result.output,
                                   retry_count=task.retry_count)
                raise Exception(result.output)

        except Exception as e:
            # Save the AI output even on failure (e.g., PatchEngine couldn't parse but code may be valid)
            if isinstance(e, Exception) and hasattr(e, '__context__'):
                pass

            # For DeepSeek agents: retry up to 3x. For Claude agents: escalate.
            if task.model == "deepseek" and task.retry_count < task.max_retry:
                task.retry_count += 1
                task.failure_reason = str(e)[:500]
                self._write_status(task.id, "failed", [], error=str(e)[:500],
                                   retry_count=task.retry_count)
                self.snapshots.rollback(snap_id)
                task.status = TaskStatus.PENDING
                transition(task, TaskStatus.READY)
                return "running"

            # Max retries exceeded — escalate to human
            self.snapshots.rollback(snap_id)
            self.scheduler.mark_failed(task, str(e))
            self._write_status(task.id, "human_required", [], error=str(e)[:500],
                               retry_count=task.retry_count)

            recovery_result = await self.recovery.handle_failure(
                task,
                AgentResult(success=False, output=str(e), files_changed=[], tokens_used=0, model=task.model),
                exec_snap,
                str(self.workspace),
            )

            if recovery_result.action.value == "escalate":
                self.scheduler.mark_human_required(task, recovery_result.reason)

            return "running"

    def _get_prompt(self, spec: AgentSpec) -> str:
        """Build system prompt from FULL agent.md content.
        For code-generation agents, append PatchEngine format instructions.
        """
        # Use the FULL agent.md as the system prompt
        base = spec.raw_md

        # For code-generation agents: enforce PatchEngine-compatible output format
        if spec.agent_type in ("backend", "frontend", "tester", "verifier"):
            base += """

=== OUTPUT FORMAT (MANDATORY) ===
Output EVERY file using this EXACT format. The PatchEngine will extract each file:
```LANG:path/to/file.ext
...complete file content...
```
Example:
```python:backend/app/main.py
from fastapi import FastAPI
app = FastAPI()
```
Write COMPLETE, RUNNABLE files. No summaries. No placeholders. No markdown descriptions between code blocks."""

        return base

    def _read_artifacts(self, meta: TaskMeta) -> dict[str, str]:
        """Read upstream artifact contents for execution snapshot."""
        artifacts: dict[str, str] = {}
        for path in meta.upstream_artifacts:
            full_path = self.workspace / path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding="utf-8")
                    artifacts[path] = ExecutionSnapshot.compute_hash(content)
                except Exception:
                    artifacts[path] = "(unreadable)"
            else:
                artifacts[path] = "(not found)"
        return artifacts

    async def run_until_done(self, max_iterations: int = 30) -> str:
        """Run the pipeline until done or blocked. Returns final status."""
        for _ in range(max_iterations):
            status = await self.run_once()
            if status in ("done", "blocked"):
                return status
        return "timeout"

    # ---- Status ----

    def status(self) -> dict:
        """Return current pipeline status including per-task states."""
        if self.graph is None:
            return {"error": "No pipeline loaded — call load_agents() first"}

        tasks = self.graph.all_tasks()
        counts: dict[str, int] = {}
        per_task: dict[str, str] = {}
        for t in tasks:
            s = t.status.value
            counts[s] = counts.get(s, 0) + 1
            per_task[t.id] = s

        return {
            "total": len(tasks),
            "by_status": counts,
            "tasks": per_task,
            "ready": len(self.graph.ready_tasks()),
            "done": self.scheduler.is_done() if self.scheduler else False,
            "blocked": self.scheduler.is_blocked() if self.scheduler else False,
            "pending_gates": self.human_gate.pending_gates(),
        }
