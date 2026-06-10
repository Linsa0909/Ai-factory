"""Tests for dag_builder.py"""
from agent_devos.agent_loader import AgentSpec, Phase
from agent_devos.artifact_registry import ArtifactRegistry, ArtifactEntry
from agent_devos.global_policy import GlobalPolicyEngine
from agent_devos.dag_builder import DAGBuilder, DAGBuildError, TaskMeta


def _make_spec(id: str, inputs: list[str], outputs: list[str]) -> AgentSpec:
    return AgentSpec(
        schema_version="1.0", agent_type=id, id=id, name=id,
        description="test", capability="test",
        inputs=inputs, outputs=outputs, phases=[], constraints=[],
        raw_md="",
    )


def test_dag_builder_creates_correct_edges():
    specs = [
        _make_spec("analyst", [], ["analysis.md"]),
        _make_spec("architect", ["analysis.md"], ["design/backend.md", "design/frontend.md"]),
        _make_spec("backend", ["design/backend.md"], ["backend/*.py"]),
        _make_spec("frontend", ["design/frontend.md"], ["frontend/*.tsx"]),
    ]
    registry = ArtifactRegistry()
    policy = GlobalPolicyEngine()

    builder = DAGBuilder()
    graph, metas = builder.build(specs, registry, policy)

    assert graph.task_count() == 4
    assert "analyst" in graph.get("architect").depends_on
    assert "architect" in graph.get("backend").depends_on
    assert "architect" in graph.get("frontend").depends_on
    assert len(graph.get("analyst").depends_on) == 0


def test_dag_builder_rejects_conflicting_producers():
    specs = [
        _make_spec("analyst", [], ["analysis.md"]),
        _make_spec("bad_agent", [], ["analysis.md"]),
    ]
    registry = ArtifactRegistry()
    policy = GlobalPolicyEngine()
    builder = DAGBuilder()

    import pytest
    with pytest.raises(DAGBuildError):
        builder.build(specs, registry, policy)


def test_dag_builder_rejects_dangling_inputs():
    specs = [
        _make_spec("architect", ["nonexistent.md"], ["design.md"]),
    ]
    registry = ArtifactRegistry()
    policy = GlobalPolicyEngine()
    builder = DAGBuilder()

    import pytest
    with pytest.raises(DAGBuildError):
        builder.build(specs, registry, policy)


def test_dag_builder_tracks_consumers_in_registry():
    specs = [
        _make_spec("analyst", [], ["analysis.md"]),
        _make_spec("architect", ["analysis.md"], ["design.md"]),
    ]
    registry = ArtifactRegistry()
    policy = GlobalPolicyEngine()
    builder = DAGBuilder()

    graph, metas = builder.build(specs, registry, policy)
    consumers = registry.get_consumers("analysis.md")
    assert "architect" in consumers


def test_dag_builder_taskmeta_populated():
    specs = [
        _make_spec("analyst", [], ["analysis.md"]),
    ]
    registry = ArtifactRegistry()
    policy = GlobalPolicyEngine()
    builder = DAGBuilder()

    graph, metas = builder.build(specs, registry, policy)
    assert "analyst" in metas
    meta = metas["analyst"]
    assert meta.agent_id == "analyst"
    assert meta.upstream_artifacts == []
    assert meta.outputs == ["analysis.md"]
    assert meta.dependency_depth == 0
