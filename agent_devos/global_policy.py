"""Global Policy Engine — system-wide semantic consistency validation.

Enforces invariants that span AgentSpec, ArtifactRegistry, and TaskGraph.
No single component can see the full picture — only GlobalPolicyEngine can.
"""

from __future__ import annotations

from agent_devos.agent_loader import AgentSpec
from agent_devos.artifact_registry import ArtifactRegistry, ArtifactEntry


class DAGBuildError(Exception):
    """Raised when DAG build fails due to policy violations."""
    pass


class AmbiguousProducerError(Exception):
    """Raised when dependency resolution cannot deterministically resolve a producer."""
    pass


class GlobalPolicyEngine:
    """Validates global system consistency across all layers."""

    def validate_before_dag_build(
        self, specs: list[AgentSpec], registry: ArtifactRegistry
    ) -> list[str]:
        """Return list of violations. Empty list = valid.
        Checks: single-writer, no dangling inputs, no semantic overwrite.
        """
        violations: list[str] = []
        violations.extend(self._check_single_writer(specs))
        violations.extend(self._check_no_dangling_inputs(specs, registry))
        violations.extend(self._check_no_semantic_overwrite(specs, registry))
        return violations

    def _check_single_writer(self, specs: list[AgentSpec]) -> list[str]:
        """No two agents may output to the same path."""
        violations: list[str] = []
        seen: dict[str, str] = {}
        for spec in specs:
            for output_path in spec.outputs:
                if output_path in seen:
                    violations.append(
                        f"Single-writer violation: '{output_path}' claimed by both "
                        f"'{seen[output_path]}' and '{spec.id}'"
                    )
                else:
                    seen[output_path] = spec.id
        return violations

    def _check_no_dangling_inputs(
        self, specs: list[AgentSpec], registry: ArtifactRegistry
    ) -> list[str]:
        """Every INPUT must have a producer (in specs or registry)."""
        violations: list[str] = []
        all_outputs: set[str] = set()
        for spec in specs:
            for o in spec.outputs:
                all_outputs.add(o)

        for spec in specs:
            for input_path in spec.inputs:
                if input_path in all_outputs:
                    continue
                if registry.lookup_producer(input_path):
                    continue
                matched = self._glob_match_any(input_path, all_outputs)
                if not matched:
                    violations.append(
                        f"Dangling input: '{spec.id}' requires '{input_path}' "
                        f"but no agent produces it"
                    )
        return violations

    def _check_no_semantic_overwrite(
        self, specs: list[AgentSpec], registry: ArtifactRegistry
    ) -> list[str]:
        """Detect overlapping glob patterns that could cause semantic overwrite."""
        violations: list[str] = []
        outputs_by_agent: dict[str, list[str]] = {}
        for spec in specs:
            outputs_by_agent[spec.id] = spec.outputs

        agent_ids = list(outputs_by_agent.keys())
        for i in range(len(agent_ids)):
            for j in range(i + 1, len(agent_ids)):
                a_id = agent_ids[i]
                b_id = agent_ids[j]
                for a_out in outputs_by_agent[a_id]:
                    for b_out in outputs_by_agent[b_id]:
                        if self._glob_patterns_overlap(a_out, b_out):
                            violations.append(
                                f"Semantic overwrite risk: '{a_id}' outputs '{a_out}' "
                                f"and '{b_id}' outputs '{b_out}' — glob patterns may overlap"
                            )
        return violations

    @staticmethod
    def _glob_match_any(path: str, candidates: set[str]) -> bool:
        """Check if path matches any candidate (exact or glob)."""
        import fnmatch
        for c in candidates:
            if fnmatch.fnmatch(path, c):
                return True
            if fnmatch.fnmatch(c, path):
                return True
        return False

    @staticmethod
    def _glob_patterns_overlap(a: str, b: str) -> bool:
        """Check if two glob patterns could match the same path.
        Conservative: returns True if they share a common prefix.
        """
        import fnmatch
        has_glob = "*" in a or "?" in a or "*" in b or "?" in b
        if not has_glob:
            return a == b

        a_dir = a.rsplit("/", 1)[0] if "/" in a else ""
        b_dir = b.rsplit("/", 1)[0] if "/" in b else ""
        return fnmatch.fnmatch(a_dir, b_dir) or fnmatch.fnmatch(b_dir, a_dir)

    def resolve_producer_by_heuristic(
        self, input_path: str, all_specs: list[AgentSpec]
    ) -> str | None:
        """Tier 4 fallback: find agent whose output path prefix matches input_path."""
        for spec in all_specs:
            for output_path in spec.outputs:
                input_dir = input_path.rsplit("/", 1)[0] if "/" in input_path else ""
                output_dir = output_path.rsplit("/", 1)[0] if "/" in output_path else ""
                if input_dir and output_dir and input_dir == output_dir:
                    return spec.id
                clean_output = output_path.replace("*", "").lstrip("/")
                if input_path.startswith(clean_output):
                    return spec.id
        return None
