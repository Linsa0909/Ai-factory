"""JSON filesystem persistence. No database."""

import json
from pathlib import Path
from typing import Any
from ai_runtime.task import Task


class RuntimeStore:
    """JSON filesystem persistence for task graph state."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace)
        self.state_dir = self.workspace / ".ai-factory" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.graph_path = self.state_dir / "task_graph.json"

    def load_graph(self) -> list[Task]:
        """Load tasks from task_graph.json. Returns empty list if file missing or corrupted."""
        if not self.graph_path.exists():
            return []
        try:
            data = json.loads(self.graph_path.read_text())
            return [Task.from_dict(t) for t in data.get("tasks", [])]
        except (json.JSONDecodeError, KeyError):
            return []

    def save_graph(self, tasks: list[Task]) -> None:
        """Persist task list to task_graph.json atomically."""
        tmp = self.graph_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"tasks": [t.to_dict() for t in tasks]}, indent=2, ensure_ascii=False
        ))
        tmp.replace(self.graph_path)

    def save_telemetry(self, entry: dict[str, Any]) -> None:
        """Append one telemetry line to JSONL file."""
        import datetime
        telemetry_dir = self.workspace / ".ai-factory" / "telemetry"
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.date.today().isoformat()
        with open(telemetry_dir / f"{date_str}.jsonl", "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def save_trace(self, task_id: str, timeline: list[dict[str, Any]]) -> None:
        """Save a trace timeline to a JSON file."""
        trace_dir = self.workspace / ".ai-factory" / "traces"
        trace_dir.mkdir(parents=True, exist_ok=True)
        (trace_dir / f"trace-{task_id}.json").write_text(json.dumps({
            "trace_id": f"trace-{task_id}", "task_id": task_id, "timeline": timeline,
        }, indent=2, ensure_ascii=False))
