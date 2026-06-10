"""AgentDevOS REST API endpoints."""
import sys
sys.path.insert(0, "/mnt/c/Users/Linsa")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter()

# Global orchestrator instance (initialized lazily)
_orchestrator = None


class SubmitRequest(BaseModel):
    feature: str
    workspace: str = ""
    requirement_text: str = ""


class GateRequest(BaseModel):
    gate_id: str
    reviewer: str = "human"
    reason: str = ""


def get_orchestrator(workspace: str = ""):
    global _orchestrator
    if _orchestrator is None:
        from agent_devos.orchestrator import Orchestrator
        ws = workspace or os.getenv("AGENTDEVOS_WORKSPACE", "/tmp/agentdevos-workspace")
        agents_dir = os.getenv("AGENTDEVOS_AGENTS_DIR", "/mnt/c/Users/Linsa/AgentDevOS/agents")
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        _orchestrator = Orchestrator(
            workspace=ws,
            agents_dir=agents_dir,
            deepseek_api_key=api_key,
        )
        _orchestrator.load_agents()
    return _orchestrator


@router.get("/status")
def get_status():
    orch = get_orchestrator()
    return orch.status()


@router.post("/submit")
def submit_feature(req: SubmitRequest):
    orch = get_orchestrator(req.workspace)
    try:
        feature_id = req.feature.upper().replace("-", "_")
        return {"feature": feature_id, "status": "submitted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/run")
async def run_once():
    orch = get_orchestrator()
    try:
        result = await orch.run_once()
        return {"result": result, "status": orch.status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gate/approve")
def gate_approve(req: GateRequest):
    orch = get_orchestrator()
    decision = orch.human_gate.approve(req.gate_id, req.reviewer)
    return {"gate": req.gate_id, "status": decision.status.value, "timestamp": decision.timestamp}


@router.post("/gate/reject")
def gate_reject(req: GateRequest):
    orch = get_orchestrator()
    decision = orch.human_gate.reject(req.gate_id, req.reason, req.reviewer)
    return {"gate": req.gate_id, "status": decision.status.value, "reason": req.reason}


@router.get("/agents")
def list_agents():
    from agent_devos.agent_loader import AgentLoader
    agents_dir = os.getenv("AGENTDEVOS_AGENTS_DIR", "/mnt/c/Users/Linsa/AgentDevOS/agents")
    specs = AgentLoader.load_all(agents_dir)
    return [{"id": s.id, "name": s.name, "description": s.description, "inputs": s.inputs, "outputs": s.outputs} for s in specs]
