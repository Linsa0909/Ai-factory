"""AgentDevOS Web Server — FastAPI entry point."""
import sys
sys.path.insert(0, "/mnt/c/Users/Linsa")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from server.api import router as api_router
from server.ws import router as ws_router

app = FastAPI(title="AgentDevOS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")

# Serve frontend static files
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")


@app.get("/health")
def health():
    return {"status": "ok", "service": "AgentDevOS"}
