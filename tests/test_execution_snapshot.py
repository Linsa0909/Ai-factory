"""Tests for execution_snapshot.py"""
from agent_devos.execution_snapshot import ExecutionSnapshot


def test_compute_context_hash_deterministic():
    hash1 = ExecutionSnapshot.compute_context_hash(
        agent_md="# Test Agent",
        upstream_artifacts={"analysis.md": "content A"},
        fsm_state={"analyst": "passed", "architect": "pending"},
        prompt_template="You are a test agent.",
    )
    hash2 = ExecutionSnapshot.compute_context_hash(
        agent_md="# Test Agent",
        upstream_artifacts={"analysis.md": "content A"},
        fsm_state={"analyst": "passed", "architect": "pending"},
        prompt_template="You are a test agent.",
    )
    assert hash1 == hash2


def test_compute_context_hash_different_input_different_hash():
    hash1 = ExecutionSnapshot.compute_context_hash(
        agent_md="# Agent A",
        upstream_artifacts={"a.md": "content"},
        fsm_state={},
        prompt_template="template",
    )
    hash2 = ExecutionSnapshot.compute_context_hash(
        agent_md="# Agent B",
        upstream_artifacts={"a.md": "content"},
        fsm_state={},
        prompt_template="template",
    )
    assert hash1 != hash2


def test_snapshot_creation():
    snap = ExecutionSnapshot(
        task_id="architect",
        timestamp="2026-06-10T00:00:00Z",
        agent_md_hash="abc123",
        context_hash="def456",
        prompt_hash="ghi789",
        artifact_versions={"analysis.md": "hash1"},
        fsm_state={"analyst": "passed"},
        model="claude",
        result_hash="",
    )
    assert snap.task_id == "architect"
    assert snap.model == "claude"


def test_can_replay_matching_context():
    snap = ExecutionSnapshot(
        task_id="test", timestamp="", agent_md_hash="", context_hash="match-me",
        prompt_hash="", artifact_versions={}, fsm_state={},
        model="deepseek", result_hash="",
    )
    assert snap.can_replay("match-me")
    assert not snap.can_replay("different")


def test_to_dict_and_from_dict():
    snap = ExecutionSnapshot(
        task_id="architect", timestamp="2026-06-10T00:00:00Z",
        agent_md_hash="abc", context_hash="def", prompt_hash="ghi",
        artifact_versions={"analysis.md": "h1"},
        fsm_state={"analyst": "passed"},
        model="claude", result_hash="jkl",
    )
    d = snap.to_dict()
    restored = ExecutionSnapshot.from_dict(d)
    assert restored.task_id == snap.task_id
    assert restored.context_hash == snap.context_hash
    assert restored.artifact_versions == snap.artifact_versions


def test_factory_create_method():
    snap = ExecutionSnapshot.create(
        task_id="architect",
        agent_md="# Architect Agent\nDesigns systems.",
        upstream_artifacts={"analysis.md": "content-hash"},
        fsm_state={"analyst": "passed"},
        prompt_template="You are an architect.",
        model="claude",
    )
    assert snap.task_id == "architect"
    assert snap.model == "claude"
    assert snap.agent_md_hash
    assert snap.context_hash
    assert snap.prompt_hash
    assert snap.result_hash == ""
    assert snap.timestamp  # Auto-generated
