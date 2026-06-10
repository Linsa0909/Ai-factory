"""Execution Snapshot — deterministic replay layer.

Every task execution records a snapshot before dispatch. This enables:
  - Debug reproducibility
  - FixLoop convergence verification
  - Audit trail for every execution
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class ExecutionSnapshot:
    """Immutable snapshot of the execution context for a single task run."""

    task_id: str
    timestamp: str
    agent_md_hash: str              # SHA256 of agent.md content
    context_hash: str               # SHA256(agent_md + upstream_artifacts + fsm_state + prompt_template)
    prompt_hash: str                # SHA256 of final assembled prompt
    artifact_versions: dict[str, str]  # path -> content_hash
    fsm_state: dict[str, str]       # task_id -> status
    model: str
    result_hash: str                # SHA256 of agent output (empty before execution)

    @staticmethod
    def compute_context_hash(
        agent_md: str,
        upstream_artifacts: dict[str, str],
        fsm_state: dict[str, str],
        prompt_template: str,
    ) -> str:
        """Deterministic hash of the full execution context.
        Binds all 4 layers of context into a single fingerprint.
        """
        payload = json.dumps({
            "agent_md": agent_md,
            "artifacts": dict(sorted(upstream_artifacts.items())),
            "fsm": dict(sorted(fsm_state.items())),
            "template": prompt_template,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA256 hash of any string content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def can_replay(self, context_hash: str) -> bool:
        """Replay is valid only if context_hash matches exactly."""
        return self.context_hash == context_hash

    def replay_diff(self, current_context_hash: str) -> dict[str, Any]:
        """Return what differs between snapshot and current state."""
        return {
            "matches": self.context_hash == current_context_hash,
            "snapshot_hash": self.context_hash,
            "current_hash": current_context_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "agent_md_hash": self.agent_md_hash,
            "context_hash": self.context_hash,
            "prompt_hash": self.prompt_hash,
            "artifact_versions": self.artifact_versions,
            "fsm_state": self.fsm_state,
            "model": self.model,
            "result_hash": self.result_hash,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExecutionSnapshot:
        """Deserialize from dictionary."""
        return cls(
            task_id=d["task_id"],
            timestamp=d["timestamp"],
            agent_md_hash=d["agent_md_hash"],
            context_hash=d["context_hash"],
            prompt_hash=d["prompt_hash"],
            artifact_versions=d["artifact_versions"],
            fsm_state=d["fsm_state"],
            model=d["model"],
            result_hash=d.get("result_hash", ""),
        )

    @classmethod
    def create(
        cls,
        task_id: str,
        agent_md: str,
        upstream_artifacts: dict[str, str],
        fsm_state: dict[str, str],
        prompt_template: str,
        model: str,
    ) -> ExecutionSnapshot:
        """Factory: create a new snapshot from execution context."""
        agent_md_hash = cls.compute_hash(agent_md)
        context_hash = cls.compute_context_hash(
            agent_md, upstream_artifacts, fsm_state, prompt_template
        )
        prompt_parts = json.dumps({
            "agent_md": agent_md,
            "artifacts": dict(sorted(upstream_artifacts.items())),
            "fsm": dict(sorted(fsm_state.items())),
        }, sort_keys=True)
        prompt_hash = hashlib.sha256(prompt_parts.encode()).hexdigest()

        return cls(
            task_id=task_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_md_hash=agent_md_hash,
            context_hash=context_hash,
            prompt_hash=prompt_hash,
            artifact_versions=upstream_artifacts,
            fsm_state=fsm_state,
            model=model,
            result_hash="",
        )
