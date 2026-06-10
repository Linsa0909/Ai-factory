"""Tests for context_assembler.py"""
import tempfile
from pathlib import Path
from agent_devos.agent_loader import AgentSpec, Phase
from agent_devos.dag_builder import TaskMeta
from agent_devos.context_assembler import ContextAssembler


def _make_spec() -> AgentSpec:
    return AgentSpec(
        schema_version="1.0", agent_type="architect", id="architect",
        name="架构师", description="设计",
        capability="设计系统架构",
        inputs=["analysis.md"], outputs=["design.md"],
        phases=[Phase(name="Phase 0: Pre-check", description="验证输入")],
        constraints=["输出 Markdown"],
        raw_md="---\nid: architect\n---\n\n# CAPABILITY\n设计系统架构",
    )


def test_context_has_four_layers():
    spec = _make_spec()
    meta = TaskMeta(
        agent_id="architect", agent_type="architect",
        upstream_artifacts=["analysis.md"],
        failure_context=["previous error: type mismatch"],
    )

    assembler = ContextAssembler()
    context = assembler.build(spec, meta, fsm_states={"analyst": "passed"})

    assert "---" in context
    assert "设计系统架构" in context       # Layer 1
    assert "Upstream Artifacts" in context  # Layer 2
    assert "FSM State" in context           # Layer 3
    assert "Failure Context" in context     # Layer 4
    assert "previous error" in context      # Layer 4 content


def test_context_layer_2_reads_artifact_files():
    spec = _make_spec()
    meta = TaskMeta(
        agent_id="architect", agent_type="architect",
        upstream_artifacts=["test_artifact.md"],
    )

    with tempfile.TemporaryDirectory() as td:
        artifact_path = Path(td) / "test_artifact.md"
        artifact_path.write_text("# Analysis Content\nThis is analysis.")

        assembler = ContextAssembler()
        context = assembler.build(spec, meta, fsm_states={}, workspace=td)

        assert "Analysis Content" in context


def test_context_layer_3_fsm_state():
    spec = _make_spec()
    meta = TaskMeta(agent_id="architect", agent_type="architect")

    assembler = ContextAssembler()
    context = assembler.build(spec, meta, fsm_states={
        "analyst": "passed",
        "architect": "pending",
        "backend": "pending",
    })

    assert "analyst: passed" in context
    assert "architect: pending" in context
