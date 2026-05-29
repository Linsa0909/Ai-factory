"""Git commit checkpoint based snapshots."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class SnapshotManager:
    """Git commit checkpoint snapshots for AI Runtime state."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace)
        self.snapshots_dir = self.workspace / ".ai-factory" / "artifacts" / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def _git(self, *args: str) -> str:
        r = subprocess.run(
            ["git", *args], cwd=self.workspace,
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr}")
        return r.stdout.strip()

    def create(self, task_id: str, reason: str, task_states: dict[str, str]) -> str:
        """Create a git commit checkpoint and return the snapshot ID."""
        snap_id = f"snap-{task_id}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
        self._git("add", "-A")
        self._git("commit", "-m", f"[AI SNAPSHOT] {snap_id} @ {task_id}: {reason}", "--allow-empty")
        commit = self._git("rev-parse", "HEAD")
        data = {
            "snapshot_id": snap_id, "git_commit": commit,
            "created_by": task_id, "reason": reason,
            "task_states": task_states, "restorable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        (self.snapshots_dir / f"{snap_id}.json").write_text(json.dumps(data, indent=2))
        return snap_id

    def rollback(self, snapshot_id: str) -> None:
        """Restore working tree to a snapshot commit."""
        snap_file = self.snapshots_dir / f"{snapshot_id}.json"
        if not snap_file.exists():
            raise FileNotFoundError(f"Snapshot {snapshot_id} not found")
        data = json.loads(snap_file.read_text())
        self._git("checkout", data["git_commit"], "--", ".")
