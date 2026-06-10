"""Context Assembler — builds 4-layer execution context for agent invocation.

Layer 1: Agent.md (CAPABILITY + EXECUTION + CONSTRAINTS)
Layer 2: Upstream Artifacts (content of input files)
Layer 3: FSM State (current pipeline status)
Layer 4: Failure History (recent error context for FixLoop)
"""

from __future__ import annotations

from pathlib import Path

from agent_devos.agent_loader import AgentSpec
from agent_devos.dag_builder import TaskMeta


class ContextAssembler:
    """Build 4-layer context for agent execution."""

    def build(
        self,
        spec: AgentSpec,
        meta: TaskMeta,
        fsm_states: dict[str, str],
        workspace: str = "",
    ) -> str:
        """Assemble the full 4-layer context string."""
        layers = [
            self._layer_1_agent_md(spec),
            self._layer_2_upstream(meta, workspace),
            self._layer_3_fsm(fsm_states),
            self._layer_4_failures(meta),
        ]
        return "\n\n---\n\n".join(layers)

    def _layer_1_agent_md(self, spec: AgentSpec) -> str:
        """Layer 1: Complete agent definition."""
        return spec.raw_md

    def _layer_2_upstream(self, meta: TaskMeta, workspace: str) -> str:
        """Layer 2: Content of upstream artifact files."""
        parts = ["## Upstream Artifacts\n"]
        if not meta.upstream_artifacts:
            parts.append("(no upstream artifacts — this is a root task)")
            return "\n".join(parts)

        ws = Path(workspace) if workspace else None
        for artifact_path in meta.upstream_artifacts:
            parts.append(f"### {artifact_path}")
            if ws:
                full_path = ws / artifact_path
                if full_path.exists():
                    try:
                        content = full_path.read_text(encoding="utf-8")
                        if len(content) > 8000:
                            parts.append(content[:8000] + "\n\n... (truncated)")
                        else:
                            parts.append(content)
                    except Exception:
                        parts.append(f"(could not read: {artifact_path})")
                else:
                    parts.append(f"(file not found: {artifact_path})")
            else:
                parts.append(f"(workspace not set — cannot read {artifact_path})")
        return "\n\n".join(parts)

    def _layer_3_fsm(self, fsm_states: dict[str, str]) -> str:
        """Layer 3: Current pipeline FSM state."""
        parts = ["## FSM State\n"]
        if not fsm_states:
            parts.append("(no FSM state available)")
        else:
            for task_id in sorted(fsm_states.keys()):
                state = fsm_states[task_id]
                parts.append(f"- {task_id}: {state}")
        return "\n".join(parts)

    def _layer_4_failures(self, meta: TaskMeta) -> str:
        """Layer 4: Recent failure context."""
        parts = ["## Failure Context\n"]
        if not meta.failure_context:
            parts.append("(no previous failures)")
        else:
            for i, ctx in enumerate(meta.failure_context, 1):
                parts.append(f"### Attempt {i}\n```\n{ctx}\n```")
        return "\n".join(parts)
