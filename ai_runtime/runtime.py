"""AIRuntime: Facade that wires all components. NO business logic."""

from pathlib import Path

from ai_runtime.task import Task
from ai_runtime.event import Event, EventType, EventBus
from ai_runtime.graph import TaskGraph
from ai_runtime.scheduler import Scheduler
from ai_runtime.store import RuntimeStore
from ai_runtime.snapshot import SnapshotManager
from ai_runtime.context import ContextBuilder
from ai_runtime.agent_adapter import AgentAdapter, AgentResult
from ai_runtime.executor import ExecutionRunner
from ai_runtime.fix_loop import AutoFixLoop, FixLoopConvergence
from ai_runtime.patch_engine import PatchEngine


PROMPTS: dict[str, str] = {
    "requirement": "You are a senior PM. Convert the feature into structured requirements: # Feature # Functional Requirements # API Design # Data Model # Edge Cases # Test Focus. Output markdown.",
    "design": "You are a senior architect. Based on requirements, generate: # Architecture # Module Breakdown # Directory Structure # Data Flow # DB Schema # Error Handling. Output markdown.",
    "testgen": "You are a senior test engineer. Generate pytest tests: unit tests, API tests, boundary tests, exception tests. Use httpx.AsyncClient. Target 85% coverage. Output Python code.",
    "dev": "You are a senior Python dev. Implement the feature: type annotations, logging, exception handling, unified response {\"code\":0,\"data\":...,\"message\":\"\"}. Do NOT modify test files. Output Python code.",
    "review": "You are a strict code reviewer. Check: null safety, concurrency, injection, resource leaks, duplicates, circular deps, edge cases, missing tests, perf, SOLID. Output markdown with HIGH/MEDIUM/LOW per issue.",
    "docs": "You are a technical writer. Generate: README.md, API docs, deploy guide. Output markdown.",
}


class AIRuntime:
    """Facade: wires components, exposes submit/status/run_once. No business logic."""

    def __init__(self, workspace: str, deepseek_api_key: str = "") -> None:
        self.workspace = Path(workspace)
        self.store = RuntimeStore(workspace)
        self.graph = TaskGraph()
        self.scheduler = Scheduler(self.graph)
        self.snapshots = SnapshotManager(workspace)
        self.context_builder = ContextBuilder(workspace)
        self.adapter = AgentAdapter(deepseek_api_key=deepseek_api_key)
        self.executor = ExecutionRunner(workspace)
        self.patcher = PatchEngine(workspace)
        # Note: fix_loop needs PatchEngine for real code changes — wired in P1
        self.fix_loop = AutoFixLoop(self.adapter, self.executor)
        self.event_bus = EventBus()

        for task in self.store.load_graph():
            self.graph.add(task)

    def _make_tasks(self, feature: str) -> list[Task]:
        fid = feature.upper().replace("-", "_")
        return [
            Task(id=f"REQ-{fid}", type="requirement", module=feature, model="claude"),
            Task(id=f"DESIGN-{fid}", type="design", depends_on=[f"REQ-{fid}"], model="claude"),
            Task(id=f"TEST-{fid}", type="testgen", depends_on=[f"DESIGN-{fid}"], model="deepseek"),
            Task(id=f"DEV-{fid}", type="dev", depends_on=[f"TEST-{fid}"], model="deepseek"),
            Task(id=f"VERIFY-{fid}", type="verify", depends_on=[f"DEV-{fid}"], model="deepseek"),
            Task(id=f"REVIEW-{fid}", type="review", depends_on=[f"VERIFY-{fid}"], model="claude"),
        ]

    async def submit(self, feature: str) -> str:
        for t in self._make_tasks(feature):
            self.graph.add(t)
        self.store.save_graph(self.graph.all_tasks())
        return feature

    async def run_once(self) -> str:
        task = self.scheduler.next_ready()
        if task is None:
            return "done" if self.scheduler.is_done() else "blocked"

        self.scheduler.dispatch(task)
        await self.event_bus.emit(Event(type=EventType.TASK_STARTED, task_id=task.id))

        states = {t.id: t.status.value for t in self.graph.all_tasks()}
        task.snapshot_before = self.snapshots.create(task.id, "before_run", states)

        try:
            result = await self._execute_task(task)
            if result.success:
                self.scheduler.mark_passed(task)
                await self.event_bus.emit(Event(type=EventType.TASK_PASSED, task_id=task.id))
            else:
                await self._handle_failure(task, result)
        except FixLoopConvergence as e:
            self.scheduler.mark_human_required(task, str(e))
            await self.event_bus.emit(Event(
                type=EventType.FIX_CONVERGENCE_FAILED, task_id=task.id, payload={"error": str(e)}
            ))

        self.store.save_graph(self.graph.all_tasks())
        return "done" if self.scheduler.is_done() else "running"

    async def run_until_done(self, feature: str) -> str:
        await self.submit(feature)
        for _ in range(30):
            result = await self.run_once()
            if result in ("done", "blocked"):
                return result
        return "timeout"

    async def _execute_task(self, task: Task) -> AgentResult:
        context = self.context_builder.build(
            task_type=task.type, module=task.module,
            failures=[task.failure_reason] if task.failure_reason else None,
        )
        prompt = PROMPTS.get(task.type, PROMPTS["dev"])
        return await self.adapter.run(task.type, prompt, context, str(self.workspace))

    async def _handle_failure(self, task: Task, result: AgentResult) -> None:
        self.scheduler.mark_failed(task, result.output[:500])
        await self.event_bus.emit(Event(
            type=EventType.TASK_FAILED, task_id=task.id, payload={"reason": result.output[:200]}
        ))

        if task.type == "verify":
            try:
                await self.fix_loop.run(task, str(self.workspace))
                self.scheduler.mark_passed(task)
                await self.event_bus.emit(Event(type=EventType.TASK_PASSED, task_id=task.id))
            except FixLoopConvergence as e:
                self.scheduler.mark_human_required(task, str(e))
                await self.event_bus.emit(Event(
                    type=EventType.FIX_CONVERGENCE_FAILED, task_id=task.id, payload={"error": str(e)}
                ))
        else:
            self.scheduler.mark_human_required(task, result.output[:500])
            await self.event_bus.emit(Event(type=EventType.TASK_HUMAN_REQUIRED, task_id=task.id))

    def status(self) -> dict:
        tasks = self.graph.all_tasks()
        counts: dict[str, int] = {}
        for t in tasks:
            s = t.status.value
            counts[s] = counts.get(s, 0) + 1
        counts["total"] = len(tasks)
        return counts
