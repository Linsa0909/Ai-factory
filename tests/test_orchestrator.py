"""Tests for orchestrator.py"""
import subprocess
import tempfile
from pathlib import Path
from agent_devos.orchestrator import Orchestrator


def test_orchestrator_loads_agents_and_builds_dag():
    """Integration test: load 8 agents, build DAG, verify structure."""
    agents_dir = "/mnt/c/Users/Linsa/AgentDevOS/agents"

    with tempfile.TemporaryDirectory() as ws:
        # SnapshotManager requires a git repo
        subprocess.run(["git", "init"], cwd=ws, capture_output=True)

        orch = Orchestrator(workspace=ws, agents_dir=agents_dir)
        specs = orch.load_agents()

        assert len(specs) == 8
        assert orch.graph is not None
        assert orch.graph.task_count() == 8
        assert orch.scheduler is not None

        # Verify DAG edges
        architect = orch.graph.get("architect")
        assert "analyst" in architect.depends_on

        backend = orch.graph.get("backend")
        assert "architect" in backend.depends_on

        frontend = orch.graph.get("frontend")
        assert "architect" in frontend.depends_on

        # Check status
        s = orch.status()
        assert s["total"] == 8
