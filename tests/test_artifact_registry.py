"""Tests for artifact_registry.py"""
from agent_devos.artifact_registry import ArtifactRegistry, ArtifactEntry


def test_register_and_lookup_producer():
    reg = ArtifactRegistry()
    entry = ArtifactEntry(
        path="{issue_id}/analysis.md",
        produced_by="analyst",
        schema_version="1.0",
        required_sections=["业务背景", "需求分析", "验收标准"],
    )
    reg.register(entry)

    producer = reg.lookup_producer("{issue_id}/analysis.md")
    assert producer == "analyst"

    assert reg.lookup_producer("nonexistent.md") is None


def test_single_writer_conflict():
    reg = ArtifactRegistry()
    reg.register(ArtifactEntry(path="design/backend.md", produced_by="architect"))
    reg.register(ArtifactEntry(path="design/frontend.md", produced_by="architect"))

    # Same path, different producer = conflict
    assert not reg.validate_no_conflict("design/backend.md", "backend")
    # Same path, same producer = no conflict (re-registration)
    assert reg.validate_no_conflict("design/backend.md", "architect")


def test_consumer_tracking():
    reg = ArtifactRegistry()
    entry = ArtifactEntry(path="analysis.md", produced_by="analyst")
    reg.register(entry)

    # Track consumers
    reg.add_consumer("analysis.md", "architect")
    reg.add_consumer("analysis.md", "tester")

    consumers = reg.get_consumers("analysis.md")
    assert set(consumers) == {"architect", "tester"}


def test_immutability_invariant_on_publish():
    reg = ArtifactRegistry()
    entry = ArtifactEntry(path="analysis.md", produced_by="analyst")
    reg.register(entry)

    # Publish the artifact
    reg.publish("analysis.md", content_hash="abc123")

    # Attempt to re-publish should fail
    assert not reg.can_publish("analysis.md", "analyst")


def test_all_entries():
    reg = ArtifactRegistry()
    reg.register(ArtifactEntry(path="a.md", produced_by="agent-a"))
    reg.register(ArtifactEntry(path="b.md", produced_by="agent-b"))

    entries = reg.all_entries()
    assert len(entries) == 2
    assert "a.md" in entries
    assert "b.md" in entries
