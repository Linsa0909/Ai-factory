"""AgentDevOS WebSocket for real-time FSM state streaming."""
import sys
sys.path.insert(0, "/mnt/c/Users/Linsa")

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

# Connected WebSocket clients
_clients: list[WebSocket] = []


@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.append(websocket)
    try:
        while True:
            # Client can send commands or just wait for status updates
            data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            msg = json.loads(data)
            if msg.get("action") == "status":
                from server.api import get_orchestrator
                orch = get_orchestrator()
                await websocket.send_json(orch.status())
    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _clients:
            _clients.remove(websocket)


async def broadcast_status(status: dict):
    """Broadcast pipeline status to all connected WebSocket clients."""
    disconnected = []
    for client in _clients:
        try:
            await client.send_json(status)
        except Exception:
            disconnected.append(client)
    for c in disconnected:
        _clients.remove(c)
