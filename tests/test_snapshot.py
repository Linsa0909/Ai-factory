"""Tests for the snapshot module."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
from ai_runtime.snapshot import SnapshotManager


def _init_git_repo(path: str | Path) -> None:
    """Initialize a git repo at path with user configured."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "initial"],
        cwd=path, capture_output=True, check=True,
    )


def test_create_produces_commit():
    """Creating a snapshot produces a git commit and metadata file."""
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        mgr = SnapshotManager(d)
        snap_id = mgr.create("T1", "test snapshot", {"T1": "running"})

        # Verify snapshot metadata was written
        snap_file = Path(d) / ".ai-factory" / "artifacts" / "snapshots" / f"{snap_id}.json"
        assert snap_file.exists()
        data = json.loads(snap_file.read_text())
        assert data["snapshot_id"] == snap_id
        assert data["created_by"] == "T1"
        assert data["reason"] == "test snapshot"
        assert data["task_states"] == {"T1": "running"}

        # Verify a git commit was created
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=d, capture_output=True, text=True, check=True,
        )
        assert snap_id in result.stdout


def test_rollback_restores_file_content():
    """Rollback restores tracked file content to snapshot state."""
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        mgr = SnapshotManager(d)

        # Create a tracked file and commit it
        test_file = Path(d) / "test.txt"
        test_file.write_text("original content")
        subprocess.run(
            ["git", "add", "test.txt"], cwd=d, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "add test file"],
            cwd=d, capture_output=True, check=True,
        )

        snap_id = mgr.create("T1", "before change", {"T1": "running"})

        # Modify the file
        test_file.write_text("modified content")
        assert test_file.read_text() == "modified content"

        # Rollback should restore original
        mgr.rollback(snap_id)
        assert test_file.read_text() == "original content"


def test_rollback_removes_untracked_files():
    """Rollback removes untracked files created after the snapshot."""
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        mgr = SnapshotManager(d)

        snap_id = mgr.create("T1", "snapshot", {"T1": "running"})

        # Create an untracked file (never committed)
        untracked = Path(d) / "should-be-removed.txt"
        untracked.write_text("this should be removed")
        assert untracked.exists()

        # Rollback should remove it
        mgr.rollback(snap_id)
        assert not untracked.exists()


def test_error_on_missing_snapshot():
    """Rolling back a non-existent snapshot raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        mgr = SnapshotManager(d)
        with pytest.raises(FileNotFoundError):
            mgr.rollback("nonexistent-snapshot")


def test_error_on_non_git_workspace():
    """Creating a SnapshotManager in a non-git directory raises RuntimeError."""
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(RuntimeError):
            SnapshotManager(d)


def test_snapshot_metadata_persisted():
    """Snapshot metadata file contains all expected fields."""
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        mgr = SnapshotManager(d)
        snap_id = mgr.create(
            "T2", "metadata test", {"T1": "running", "T2": "pending"},
        )
        snap_file = Path(d) / ".ai-factory" / "artifacts" / "snapshots" / f"{snap_id}.json"
        data = json.loads(snap_file.read_text())

        assert data["snapshot_id"] == snap_id
        assert data["created_by"] == "T2"
        assert data["reason"] == "metadata test"
        assert data["task_states"] == {"T1": "running", "T2": "pending"}
        assert data["restorable"] is True
        assert "timestamp" in data
        assert "git_commit" in data
