"""Tests for the context builder module."""

import tempfile
from pathlib import Path

from ai_runtime.context import ContextBuilder


def test_build_reads_requirement_and_design():
    """Context includes content from both requirement.md and design.md."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, "docs").mkdir()
        Path(d, "docs", "requirement.md").write_text("Requirement content.")
        Path(d, "docs", "design.md").write_text("Design content.")
        builder = ContextBuilder(d)
        ctx = builder.build("codegen")
        assert "Requirement" in ctx
        assert "Design" in ctx


def test_truncation_at_500_words():
    """Documents longer than 500 words are truncated with a marker."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, "docs").mkdir()
        Path(d, "docs", "requirement.md").write_text("word " * 600)
        builder = ContextBuilder(d)
        ctx = builder.build("codegen")
        assert "[...truncated]" in ctx


def test_empty_workspace_returns_empty_string():
    """Build returns empty string when there are no docs and no failures."""
    with tempfile.TemporaryDirectory() as d:
        builder = ContextBuilder(d)
        ctx = builder.build("codegen")
        assert ctx == ""


def test_failures_appended():
    """Recent failures appear in the context, limited to the last 3."""
    with tempfile.TemporaryDirectory() as d:
        builder = ContextBuilder(d)
        failures = ["fail 1", "fail 2", "fail 3", "fail 4"]
        ctx = builder.build("codegen", failures=failures)
        # Only last 3 failures should be included
        assert "fail 2" in ctx
        assert "fail 3" in ctx
        assert "fail 4" in ctx
        assert "fail 1" not in ctx


def test_missing_docs_handled_gracefully():
    """Empty docs directory does not cause errors."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, "docs").mkdir()
        builder = ContextBuilder(d)
        ctx = builder.build("codegen")
        assert ctx == ""


def test_read_error_handled_gracefully():
    """Files that cause UnicodeDecodeError are skipped without crashing."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, "docs").mkdir()
        doc_path = Path(d, "docs", "requirement.md")
        # Write invalid UTF-8 bytes to trigger UnicodeDecodeError
        doc_path.write_bytes(b"\xff")
        builder = ContextBuilder(d)
        ctx = builder.build("codegen")
        assert ctx == ""
