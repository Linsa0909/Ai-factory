"""DAG Builder — generates execution graph from AgentSpec + ArtifactRegistry + Policy.

Dependency resolution follows a deterministic 4-tier priority:
  Tier 1: Artifact Registry (explicit producer registration)
  Tier 2: Explicit INPUT declaration in agent.md
  Tier 3: OUTPUT inference fallback (glob match against all agent outputs)
  Tier 4: Naming heuristic (path prefix convention)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_devos.agent_loader import AgentSpec
from agent_devos.artifact_registry import ArtifactRegistry, ArtifactEntry, AmbiguousProducerError
from agent_devos.global_policy import GlobalPolicyEngine, DAGBuildError

# Import ai_runtime types (read-only dependency)
import sys
sys.path.insert(0, "/mnt/c/Users/Linsa/ai-factory-runtime")
from ai_runtime.task import Task, TaskStatus
from ai_runtime.graph import TaskGraph


@dataclass
class TaskMeta:
    """AgentDevOS-specific metadata attached to each Task.
    Stored separately from ai_runtime.Task to keep ai-factory-runtime read-only.
    """
    agent_id: str
    agent_type: str
    upstream_artifacts: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    dependency_depth: int = 0
    priority: int = 0
    artifact_wait_time: float = 0.0
    failure_context: list[str] = field(default_factory=list)


class DAGBuilder:
    """Build a TaskGraph from AgentSpec definitions."""

    def build(
        self,
        specs: list[AgentSpec],
        registry: ArtifactRegistry,
        policy: GlobalPolicyEngine,
    ) -> tuple[TaskGraph, dict[str, TaskMeta]]:
        """Build a TaskGraph and metadata dict from agent specs.
        Returns (graph, metas) where metas is {task_id: TaskMeta}.
        Raises DAGBuildError if policy violations are found.
        """
        # Step 1: Register all artifact outputs
        for spec in specs:
            for output_path in spec.outputs:
                try:
                    registry.register(ArtifactEntry(
                        path=output_path,
                        produced_by=spec.id,
                        schema_version=spec.schema_version,
                        consumers=[],
                    ))
                except AmbiguousProducerError as e:
                    raise DAGBuildError(
                        f"DAG build failed: {e}"
                    ) from e

        # Step 2: Global policy validation (Tier 1: strongest constraint)
        violations = policy.validate_before_dag_build(specs, registry)
        if violations:
            raise DAGBuildError(
                f"DAG build failed with {len(violations)} policy violation(s):\n" +
                "\n".join(f"  - {v}" for v in violations)
            )

        # Step 3: Infer dependency edges (Tiers 2-4)
        graph = TaskGraph()
        metas: dict[str, TaskMeta] = {}

        for spec in specs:
            deps = self._resolve_dependencies(spec, specs, registry, policy)
            task = Task(
                id=spec.id,
                type=spec.agent_type,
                module=spec.id,
                depends_on=deps,
                model="claude" if spec.agent_type in ("analyst", "architect", "recorder", "knowledge") else "deepseek",
            )
            graph.add(task)

            # Track consumers in registry
            for input_path in spec.inputs:
                actual_producer = self._find_producer(input_path, specs, registry, policy)
                if actual_producer:
                    try:
                        registry.add_consumer(input_path, spec.id)
                    except KeyError:
                        pass  # User-provided artifacts won't be in registry

            # Build TaskMeta
            meta = TaskMeta(
                agent_id=spec.id,
                agent_type=spec.agent_type,
                upstream_artifacts=spec.inputs,
                outputs=spec.outputs,
                dependency_depth=len(deps),
            )
            metas[spec.id] = meta

        # Step 4: Compute final dependency depths (BFS from roots)
        self._compute_depths(metas, graph)

        # Step 5: Validate the graph
        graph.validate()
        return graph, metas

    def _resolve_dependencies(
        self,
        spec: AgentSpec,
        all_specs: list[AgentSpec],
        registry: ArtifactRegistry,
        policy: GlobalPolicyEngine,
    ) -> list[str]:
        """Resolve dependencies for a single agent spec.
        Returns list of task_ids this agent depends on.
        """
        deps: list[str] = []
        for input_path in spec.inputs:
            producer = self._find_producer(input_path, all_specs, registry, policy)
            if producer and producer != spec.id:
                if producer not in deps:
                    deps.append(producer)
        return deps

    def _find_producer(
        self,
        input_path: str,
        all_specs: list[AgentSpec],
        registry: ArtifactRegistry,
        policy: GlobalPolicyEngine,
    ) -> str | None:
        """Find the producer for an input path using 4-tier resolution."""
        # Tier 1: Artifact Registry (strongest)
        producer = registry.lookup_producer(input_path)
        if producer:
            return producer

        # Tier 2: Explicit INPUT/OUTPUT match in specs
        for s in all_specs:
            if input_path in s.outputs:
                return s.id

        # Tier 3: Glob match against all outputs
        import fnmatch
        for s in all_specs:
            for output in s.outputs:
                if fnmatch.fnmatch(input_path, output) or fnmatch.fnmatch(output, input_path):
                    return s.id

        # Tier 4: Naming heuristic
        return policy.resolve_producer_by_heuristic(input_path, all_specs)

    def _compute_depths(self, metas: dict[str, TaskMeta], graph: TaskGraph) -> None:
        """Compute dependency_depth via BFS from root nodes."""
        roots = [t for t in graph.all_tasks() if not t.depends_on]
        from collections import deque
        visited: set[str] = set()
        q = deque(roots)
        while q:
            task = q.popleft()
            visited.add(task.id)
            for other in graph.all_tasks():
                if task.id in other.depends_on:
                    new_depth = metas[task.id].dependency_depth + 1
                    if new_depth > metas[other.id].dependency_depth:
                        metas[other.id].dependency_depth = new_depth
                    if other.id not in visited:
                        q.append(other)
