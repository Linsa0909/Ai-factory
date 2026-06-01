import asyncio
import subprocess
import tempfile
from pathlib import Path

from ai_runtime.runtime import AIRuntime, PROMPTS
from ai_runtime.task import TaskStatus


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


def test_runtime_creates_without_error():
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        rt = AIRuntime(d)
        assert rt.workspace is not None
        assert rt.graph is not None
        assert rt.scheduler is not None


async def test_submit_creates_6_tasks():
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        rt = AIRuntime(d)
        feature = await rt.submit("todo-crud")
        assert feature == "todo-crud"
        assert rt.graph.task_count() == 6


async def test_submit_tasks_form_linear_dag():
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        rt = AIRuntime(d)
        await rt.submit("todo-crud")
        tasks = rt.graph.all_tasks()
        ids = {t.id for t in tasks}
        assert "REQ-TODO_CRUD" in ids
        assert "DESIGN-TODO_CRUD" in ids
        assert "TEST-TODO_CRUD" in ids
        assert "DEV-TODO_CRUD" in ids
        assert "VERIFY-TODO_CRUD" in ids
        assert "REVIEW-TODO_CRUD" in ids


def test_status_counts_tasks():
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        rt = AIRuntime(d)
        s = rt.status()
        assert s["total"] == 0
        assert s.get("pending", 0) == 0


async def test_run_once_on_empty_graph_returns_done():
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        rt = AIRuntime(d)
        result = await rt.run_once()
        assert result == "done"


def test_scheduler_picks_root_task():
    """Submit a feature and verify scheduler picks the root task."""
    with tempfile.TemporaryDirectory() as d:
        _init_git_repo(d)
        rt = AIRuntime(d)
        # Test that scheduler returns tasks after submit
        asyncio.run(rt.submit("test-feature"))
        # After submit, root task REQ-TEST_FEATURE should be PENDING
        req = rt.graph.get("REQ-TEST_FEATURE")
        assert req.status == TaskStatus.PENDING

        # Scheduler should return root task as ready
        t = rt.scheduler.next_ready()
        assert t is not None
        assert t.id == "REQ-TEST_FEATURE"

        # Dispatch through scheduler directly (bypasses agent adapter)
        rt.scheduler.dispatch(t)
        assert t.status == TaskStatus.RUNNING


def test_prompts_have_all_task_types():
    assert "requirement" in PROMPTS
    assert "design" in PROMPTS
    assert "testgen" in PROMPTS
    assert "dev" in PROMPTS
    assert "review" in PROMPTS
    assert "docs" in PROMPTS
