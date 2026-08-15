"""
HoneyNet FastAPI Application
Central backend orchestrator for adaptive honeypot monitoring,
WebSocket real-time telemetry, and MITRE threat intelligence.
"""
import threading
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import COWRIE_LOG_PATH, OLLAMA_MODEL, OLLAMA_URL
from backend.db import (
    init_db,
    get_all_sessions,
    get_session_by_id,
    get_events_by_session,
    get_all_events,
    get_overview_metrics,
    get_all_assets,
    get_mitre_statistics,
    record_event
)
from backend.classifier import (
    check_ollama_health,
    warmup_classifier,
    classify_command,
    generate_attacker_summary
)
from backend.mitre_mapper import map_command_to_mitre
from backend.asset_manager import seed_honeyfs_from_templates
from backend.expansion_engine import build_attack_path_graph
from backend.log_tailer import CowrieLogTailer
from backend.ws_manager import ws_manager, set_main_event_loop, broadcast_sync
from backend.models import SimulatorTriggerRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("honeynet.api")

tailer_instance = CowrieLogTailer()
tailer_thread: Optional[threading.Thread] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database, seed honeyfs, pre-warm LLM, launch background tailer."""
    logger.info("Initializing HoneyNet SQLite/Postgres Database...")
    init_db()
    
    # Store main event loop for thread-safe WebSocket broadcasts
    loop = asyncio.get_running_loop()
    set_main_event_loop(loop)

    logger.info("Ensuring HoneyFS virtual filesystem is seeded...")
    seed_honeyfs_from_templates()
    
    logger.info("Checking Ollama AI health and pre-warming...")
    warmup_classifier()
    
    global tailer_thread
    logger.info("Starting Cowrie Log Tailer background worker...")
    tailer_thread = threading.Thread(target=tailer_instance.run_loop, args=(0.5,), daemon=True)
    tailer_thread.start()
    
    yield
    
    logger.info("Shutting down HoneyNet background worker...")
    tailer_instance.stop()

app = FastAPI(
    title="HoneyNet AI Adaptive Honeypot API",
    description="Real-time attacker intent classification and forensic telemetry API",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js and external dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# WebSocket Endpoint for Live SOC Streaming
# -----------------------------------------------------------------------------
@app.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    """Real-time bidirectional WebSocket stream for live command feeds and risk alerts."""
    await ws_manager.connect(websocket)
    try:
        # Send initial welcome and snapshot
        overview = get_overview_metrics()
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "message": "Connected to HoneyNet Real-Time Threat Stream",
                "overview": overview
            }
        })
        while True:
            # Keep connection alive and accept optional client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "HoneyNet AI Adaptive Honeynet SOC Core",
        "status": "operational",
        "version": "2.0.0",
        "docs": "/docs",
        "websocket": "/ws/live"
    }

@app.get("/api/status")
def get_system_status():
    """System health check including Ollama connectivity and log file status."""
    ollama_ok, ollama_msg = check_ollama_health()
    return {
        "status": "healthy",
        "ollama": {
            "available": ollama_ok,
            "url": OLLAMA_URL,
            "model": OLLAMA_MODEL,
            "status_message": ollama_msg
        },
        "cowrie_log": {
            "path": str(COWRIE_LOG_PATH),
            "exists": COWRIE_LOG_PATH.exists(),
            "size_bytes": COWRIE_LOG_PATH.stat().st_size if COWRIE_LOG_PATH.exists() else 0
        },
        "active_ws_clients": len(ws_manager.active_connections)
    }

@app.get("/api/overview")
def get_dashboard_overview():
    """Returns top-level SOC telemetry metrics."""
    metrics = get_overview_metrics()
    ollama_ok, _ = check_ollama_health()
    metrics["ollama_status"] = "Active" if ollama_ok else "Heuristic Mode"
    metrics["cowrie_status"] = "Active" if COWRIE_LOG_PATH.exists() else "Standby"
    return metrics

@app.get("/api/sessions")
def list_sessions():
    """Returns all attacker sessions ordered by last activity."""
    return get_all_sessions()

@app.get("/api/sessions/{session_id}")
def get_session_detail(session_id: str):
    """Returns full forensic details for a specific session."""
    session = get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    events = get_events_by_session(session_id)
    return {
        "session": session,
        "events": events
    }

@app.get("/api/events")
def list_events(
    session_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """Returns recent command execution events with optional filters."""
    if session_id:
        events = get_events_by_session(session_id)
    else:
        events = get_all_events(limit=limit)
    if category and category != "all":
        events = [e for e in events if e.get("category") == category]
    return events

@app.get("/api/attack-path/{session_id}")
def get_session_attack_path(session_id: str):
    """Constructs React Flow graph nodes and edges representing attacker lateral movement."""
    session = get_session_by_id(session_id)
    if not session:
        # Return base topology if session not found
        return build_attack_path_graph([], 0)
    cats = session.get("categories_triggered", [])
    risk = session.get("risk_score", 10)
    return build_attack_path_graph(cats, risk)

@app.get("/api/mitre-matrix")
def get_mitre_matrix():
    """Aggregates all triggered MITRE ATT&CK techniques with counts and samples."""
    return get_mitre_statistics()

@app.get("/api/assets")
def list_assets():
    """Returns all dynamically generated deception assets."""
    return get_all_assets()

# -----------------------------------------------------------------------------
# Attack Simulator Trigger API (For Dashboard & Live Demos)
# -----------------------------------------------------------------------------
@app.post("/api/simulator/trigger")
def trigger_attack_simulation(req: SimulatorTriggerRequest):
    """
    Triggers an automated simulated attacker scenario in a background thread.
    Ideal for testing and evaluation without external attackers.
    """
    from honeypot_sim import run_simulation
    
    scenarios = [req.scenario] if req.scenario != "full_apt" else ["git", "aws", "finance", "hr"]
    
    def _sim_worker():
        try:
            run_simulation(
                mode="file",
                scenarios_to_run=scenarios,
                delay=req.delay,
                override_ip=req.ip
            )
        except Exception as e:
            logger.error(f"Simulator trigger error: {e}")

    threading.Thread(target=_sim_worker, daemon=True).start()
    
    return {
        "status": "triggered",
        "scenario": req.scenario,
        "scenarios_queued": scenarios,
        "message": f"Simulation scenario '{req.scenario}' started successfully."
    }
