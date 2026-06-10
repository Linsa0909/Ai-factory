"""Tests for global_policy.py"""
from agent_devos.agent_loader import AgentSpec, Phase
from agent_devos.artifact_registry import ArtifactRegistry, ArtifactEntry
from agent_devos.global_policy import GlobalPolicyEngine


def _make_spec(id: str, inputs: list[str], outputs: list[str]) -> AgentSpec:
    return AgentSpec(
        schema_version="1.0", agent_type=id, id=id, name=id,
        description="test", capability="test",
        inputs=inputs, outputs=outputs, phases=[], constraints=[],
        raw_md="",
    )


def test_single_writer_violation_detected():
    policy = GlobalPolicyEngine()
    specs = [
        _make_spec("analyst", [], ["analysis.md"]),
        _make_spec("bad_agent", [], ["analysis.md"]),
    ]
    registry = ArtifactRegistry()

    violations = policy.validate_before_dag_build(specs, registry)
    assert len(violations) > 0
    assert any("analysis.md" in v for v in violations)


def test_dangling_input_detected():
    policy = GlobalPolicyEngine()
    specs = [
        _make_spec("architect", ["analysis.md", "nonexistent.md"], ["design.md"]),
    ]
    registry = ArtifactRegistry()
    violations = policy.validate_before_dag_build(specs, registry)
    assert len(violations) > 0
    assert any("nonexistent" in v for v in violations)


def test_valid_specs_pass_all_checks():
    policy = GlobalPolicyEngine()
    specs = [
        _make_spec("analyst", [], ["analysis.md"]),
        _make_spec("architect", ["analysis.md"], ["design.md"]),
        _make_spec("backend", ["design.md"], ["backend/*.py"]),
    ]
    registry = ArtifactRegistry()
    for s in specs:
        for o in s.outputs:
            registry.register(ArtifactEntry(path=o, produced_by=s.id))

    violations = policy.validate_before_dag_build(specs, registry)
    assert len(violations) == 0


def test_no_semantic_overwrite_via_glob():
    policy = GlobalPolicyEngine()
    specs = [
        _make_spec("backend", [], ["backend/app/*.py"]),
        _make_spec("frontend", [], ["frontend/app/*.tsx"]),
    ]
    registry = ArtifactRegistry()

    violations = policy.validate_before_dag_build(specs, registry)
    assert len(violations) == 0


def test_dependency_resolution_tier4_heuristic():
    policy = GlobalPolicyEngine()
    producer = policy.resolve_producer_by_heuristic(
        input_path="analysis.md",
        all_specs=[
            _make_spec("analyst", [], ["analysis.md"]),
            _make_spec("architect", [], ["design.md"]),
        ],
    )
    assert producer == "analyst"
