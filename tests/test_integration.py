"""Full pipeline integration tests — 8-agent DAG topology, artifact registry, agent loading."""
import tempfile
from agent_devos.orchestrator import Orchestrator


def test_full_8_agent_dag_structure():
    """Verify the full 8-agent DAG has correct dependency topology."""
    agents_dir = "/mnt/c/Users/Linsa/AgentDevOS/agents"

    with tempfile.TemporaryDirectory() as ws:
        import subprocess
        subprocess.run(["git", "init"], cwd=ws, capture_output=True)

        orch = Orchestrator(workspace=ws, agents_dir=agents_dir)
        orch.load_agents()

        assert orch.graph is not None
        graph = orch.graph

        expected_ids = {"analyst", "architect", "backend", "frontend",
                        "tester", "verifier", "recorder", "knowledge"}
        actual_ids = {t.id for t in graph.all_tasks()}
        assert actual_ids == expected_ids

        tasks = {t.id: t for t in graph.all_tasks()}

        # analyst: root, no deps
        assert tasks["analyst"].depends_on == []

        # architect: depends on analyst
        assert "analyst" in tasks["architect"].depends_on

        # backend + frontend: both depend on architect
        assert "architect" in tasks["backend"].depends_on
        assert "architect" in tasks["frontend"].depends_on

        # tester: depends on backend AND frontend
        assert "backend" in tasks["tester"].depends_on
        assert "frontend" in tasks["tester"].depends_on

        # verifier: depends on tester
        assert "tester" in tasks["verifier"].depends_on

        # recorder: depends on verifier
        assert "verifier" in tasks["recorder"].depends_on

        # knowledge: depends on recorder (last)
        assert "recorder" in tasks["knowledge"].depends_on

        # Verify task types match agent types
        for t in graph.all_tasks():
            meta = orch.metas.get(t.id)
            assert meta is not None, f"No TaskMeta for {t.id}"
            assert meta.agent_id == t.id
            assert meta.agent_type in expected_ids


def test_artifact_registry_has_all_producers():
    """Verify every agent output is registered in the ArtifactRegistry."""
    agents_dir = "/mnt/c/Users/Linsa/AgentDevOS/agents"

    with tempfile.TemporaryDirectory() as ws:
        import subprocess
        subprocess.run(["git", "init"], cwd=ws, capture_output=True)

        orch = Orchestrator(workspace=ws, agents_dir=agents_dir)
        orch.load_agents()

        entries = orch.registry.all_entries()

        for spec in orch.specs:
            agent_outputs = [p for p, e in entries.items() if e.produced_by == spec.id]
            assert len(agent_outputs) > 0, f"Agent {spec.id} has no registered outputs"


def test_all_agent_md_files_loadable():
    """Verify all 8 agent.md files parse without errors."""
    from agent_devos.agent_loader import AgentLoader
    specs = AgentLoader.load_all("/mnt/c/Users/Linsa/AgentDevOS/agents")
    assert len(specs) == 8

    required_ids = {"analyst", "architect", "backend", "frontend",
                    "tester", "verifier", "recorder", "knowledge"}
    for spec in specs:
        assert spec.id in required_ids
        assert spec.schema_version == "1.0"
        assert spec.agent_type == spec.id
        assert spec.capability
        assert len(spec.outputs) > 0
