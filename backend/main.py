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

from backend.config import COWRIE_LOG_PATH, OLLAMA_MODEL, OLLAMA_URL
from backend.db import (
    init_db,
    get_all_sessions,
    get_session_by_id,
    get_all_events,
    get_overview_metrics,
    get_all_assets,
    get_mitre_statistics
)
from backend.classifier import (
    check_ollama_health,
    warmup_classifier,
    classify_command
)
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
    logger.info("Initializing HoneyNet Embedded-Document Database...")
    init_db()
    
    # Store main event loop for thread-safe WebSocket broadcasts
    loop = asyncio.get_running_loop()
    set_main_event_loop(loop)

    logger.info("Ensuring HoneyFS virtual filesystem is seeded...")
    try:
        seed_honeyfs_from_templates()
    except Exception as e:
        logger.warning(f"HoneyFS seed warning: {e}")

    logger.info("Checking native Ollama LLM readiness...")
    warmup_classifier()

    # Start background Cowrie log tailer
    global tailer_thread
    tailer_thread = threading.Thread(
        target=tailer_instance.run_loop,
        kwargs={"poll_interval": 0.5},
        daemon=True
    )
    tailer_thread.start()
    logger.info("HoneyNet Ingestion & Defense Core is fully armed.")

    yield

    # Cleanup on shutdown
    logger.info("Stopping HoneyNet Log Tailer...")
    tailer_instance.stop()

app = FastAPI(
    title="HoneyNet Forensics Core",
    description="AI-Driven Cyber Deception & Autonomous Honeytoken Infrastructure",
    version="2.1.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# WebSocket Live Streaming Endpoint
# -----------------------------------------------------------------------------
@app.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    """
    Bidirectional WebSocket connection for live telemetry streaming.
    Pushes:
      - 'command_event' (real-time adversary inputs & risk scores)
      - 'asset_created' (dynamic honeytokens deployed)
      - 'threat_alert' (severity threshold breaches)
    """
    await ws_manager.connect(websocket)
    try:
        # Push initial status handshake
        await websocket.send_json({
            "type": "handshake",
            "message": "Connected to HoneyNet Real-Time Telemetry Bus",
            "active_clients": len(ws_manager.active_connections)
        })
        while True:
            # Keep-alive heartbeat & ping receiver
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket client disconnected ({e})")
        ws_manager.disconnect(websocket)

# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "HoneyNet AI Adaptive Honeynet SOC Core",
        "status": "operational",
        "version": "2.1.0",
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
    metrics.ollama_status = "Active (Native M4)" if ollama_ok else "Heuristic Engine"
    metrics.cowrie_status = "Listening (:2222)" if COWRIE_LOG_PATH.exists() else "Standby"
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
    return session

@app.get("/api/events")
def list_events(
    session_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """Returns recent command execution events with optional filters."""
    events = get_all_events(limit=limit)
    if session_id:
        events = [e for e in events if e.session_id == session_id]
    if category and category != "all":
        events = [e for e in events if e.category == category]
    return events

@app.get("/api/attack-path/{session_id}")
def get_session_attack_path(session_id: str):
    """Constructs React Flow graph nodes and edges representing attacker lateral movement."""
    session = get_session_by_id(session_id)
    if not session:
        return build_attack_path_graph([], 0)
    cats = session.categories_triggered
    risk = session.attacker_profile.risk_score
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
    
    scenarios = [req.scenario] if req.scenario != "full_apt" else ["finance", "git", "aws"]
    
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
        "delay": req.delay,
        "message": f"Simulation scenario '{req.scenario}' started successfully."
    }
