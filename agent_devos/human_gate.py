"""Human Gate — Review / Approve / Reject for human-in-the-loop checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone


class GateStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class GateDecision:
    gate_id: str
    status: GateStatus
    reviewer: str = ""
    reason: str = ""
    timestamp: str = ""

    @classmethod
    def approve(cls, gate_id: str, reviewer: str = "human") -> GateDecision:
        return cls(
            gate_id=gate_id,
            status=GateStatus.APPROVED,
            reviewer=reviewer,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def reject(cls, gate_id: str, reason: str, reviewer: str = "human") -> GateDecision:
        return cls(
            gate_id=gate_id,
            status=GateStatus.REJECTED,
            reviewer=reviewer,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class HumanGate:
    """Manages human-in-the-loop gates: Review / Approve / Reject.

    Gates:
      - Gate1: require -> design (requirement review)
      - Gate2: test -> dev (test plan review)
      - Gate3: review -> deploy (final code review)
    """

    GATE_ORDER = ["gate1", "gate2", "gate3"]

    def __init__(self) -> None:
        self._gates: dict[str, GateDecision] = {}
        self._current_gate: str | None = None

    def create_gate(self, gate_id: str, task_from: str, task_to: str) -> None:
        """Create a pending gate between two tasks."""
        self._gates[gate_id] = GateDecision(
            gate_id=gate_id,
            status=GateStatus.PENDING,
        )
        self._current_gate = gate_id

    def approve(self, gate_id: str, reviewer: str = "human") -> GateDecision:
        """Approve a gate, allowing the pipeline to proceed."""
        if gate_id not in self._gates:
            raise KeyError(f"Gate '{gate_id}' not found")
        decision = GateDecision.approve(gate_id, reviewer)
        self._gates[gate_id] = decision
        if self._current_gate == gate_id:
            self._current_gate = None
        return decision

    def reject(self, gate_id: str, reason: str, reviewer: str = "human") -> GateDecision:
        """Reject a gate, blocking the pipeline."""
        if gate_id not in self._gates:
            raise KeyError(f"Gate '{gate_id}' not found")
        decision = GateDecision.reject(gate_id, reason, reviewer)
        self._gates[gate_id] = decision
        return decision

    def is_approved(self, gate_id: str) -> bool:
        """Check if a gate is approved."""
        decision = self._gates.get(gate_id)
        return decision is not None and decision.status == GateStatus.APPROVED

    def is_blocked(self) -> bool:
        """Check if the pipeline is blocked at a gate."""
        if self._current_gate is None:
            return False
        decision = self._gates.get(self._current_gate)
        return decision is not None and decision.status == GateStatus.PENDING

    def pending_gates(self) -> list[str]:
        """Return list of pending gate IDs."""
        return [
            gid for gid, d in self._gates.items()
            if d.status == GateStatus.PENDING
        ]

    def current_gate(self) -> str | None:
        """Return the current pending gate, or None."""
        return self._current_gate
