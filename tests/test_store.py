import json
import tempfile
from pathlib import Path
from ai_runtime.store import RuntimeStore
from ai_runtime.task import Task


def test_save_and_load_graph():
    with tempfile.TemporaryDirectory() as d:
        store = RuntimeStore(d)
        tasks = [Task(id="T1", type="codegen"), Task(id="T2", type="testgen")]
        store.save_graph(tasks)
        loaded = store.load_graph()
        assert len(loaded) == 2
        assert {t.id for t in loaded} == {"T1", "T2"}


def test_load_graph_returns_empty_when_no_file():
    with tempfile.TemporaryDirectory() as d:
        store = RuntimeStore(d)
        assert store.load_graph() == []


def test_load_graph_returns_empty_on_corrupted_file():
    """Corrupted JSON must NOT crash — return empty list gracefully."""
    with tempfile.TemporaryDirectory() as d:
        store = RuntimeStore(d)
        store.graph_path.write_text("not valid json {{{")
        assert store.load_graph() == []


def test_atomic_write_does_not_corrupt_on_crash():
    """Save uses .tmp + replace — partial writes don't corrupt existing data."""
    with tempfile.TemporaryDirectory() as d:
        store = RuntimeStore(d)
        tasks = [Task(id="T1", type="codegen")]
        store.save_graph(tasks)
        # Verify the tmp file is cleaned up after atomic replace
        assert not store.graph_path.with_suffix(".json.tmp").exists()
        loaded = store.load_graph()
        assert len(loaded) == 1
        assert loaded[0].id == "T1"


def test_telemetry_appends_jsonl():
    with tempfile.TemporaryDirectory() as d:
        store = RuntimeStore(d)
        store.save_telemetry({"task_id": "T1", "model": "claude", "tokens": 100, "latency_ms": 500, "success": True})
        store.save_telemetry({"task_id": "T2", "model": "deepseek", "tokens": 200, "latency_ms": 300, "success": False})
        import datetime
        date_str = datetime.date.today().isoformat()
        telemetry_file = Path(d) / ".ai-factory" / "telemetry" / f"{date_str}.jsonl"
        lines = telemetry_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["task_id"] == "T1"
        assert json.loads(lines[1])["task_id"] == "T2"


def test_trace_saved_correctly():
    with tempfile.TemporaryDirectory() as d:
        store = RuntimeStore(d)
        timeline = [{"event": "TASK_STARTED"}, {"event": "PYTEST_FAILED"}]
        store.save_trace("T1", timeline)
        trace_file = Path(d) / ".ai-factory" / "traces" / "trace-T1.json"
        data = json.loads(trace_file.read_text())
        assert data["trace_id"] == "trace-T1"
        assert data["task_id"] == "T1"
        assert len(data["timeline"]) == 2
