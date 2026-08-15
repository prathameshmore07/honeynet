"""
HoneyNet FastAPI Application
Central backend orchestrator for adaptive honeypot monitoring,
WebSocket real-time telemetry, and MITRE threat intelligence.
Hardened with rate-limiting, CORS origin restrictions, and strict response models.
"""
import time
import threading
import logging
import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings, COWRIE_LOG_PATH, OLLAMA_MODEL, OLLAMA_URL
from backend.db import (
    init_db,
    get_all_sessions,
    get_session_by_id,
    get_all_events,
    get_overview_metrics,
    get_all_assets,
    get_mitre_statistics,
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
from backend.models import (
    OverviewMetrics,
    SessionSummary,
    SessionDoc,
    CommandEvent,
    AttackPathGraph,
    MitreTechniqueStat,
    GeneratedAsset,
    SimulatorTriggerRequest
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("honeynet.api")

tailer_instance = CowrieLogTailer()
tailer_thread: Optional[threading.Thread] = None

# In-memory sliding window rate limiter
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_history = defaultdict(list)
        self.lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        # Check client IP or forwarded IP
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
        
        # Local development dashboard is exempted from rate limiting unless testing external IP
        if not forwarded and client_ip in ("127.0.0.1", "localhost", "::1"):
            return await call_next(request)

        now = time.time()
        
        with self.lock:
            # Clean old entries
            timestamps = self.request_history[client_ip]
            cutoff = now - self.window_seconds
            self.request_history[client_ip] = [t for t in timestamps if t > cutoff]
            
            if len(self.request_history[client_ip]) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return Response(
                    content='{"detail":"Too Many Requests — Rate limit exceeded"}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json"
                )
            self.request_history[client_ip].append(now)

        return await call_next(request)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database, seed honeyfs, pre-warm LLM, launch background tailer."""
    logger.info("Initializing HoneyNet Database & Deception Core...")
    init_db()
    
    # Store main event loop for thread-safe WebSocket broadcasts
    loop = asyncio.get_running_loop()
    set_main_event_loop(loop)

    logger.info("Ensuring HoneyFS virtual filesystem is seeded...")
    try:
        seed_honeyfs_from_templates()
    except Exception as e:
        logger.warning(f"HoneyFS seed warning: {e}")

    logger.info("Checking native Ollama LLM readiness on Apple Silicon...")
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
    version="2.2.0",
    lifespan=lifespan
)

# Rate Limiter Middleware
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)

# CORS Configuration with Explicit Allowed Origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# WebSocket Live Streaming Endpoint (Authenticated)
# -----------------------------------------------------------------------------
@app.websocket("/ws/live")
async def websocket_live_feed(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Bidirectional WebSocket connection for live telemetry streaming.
    Supports optional auth token check (?token=...) with dev fallback.
    """
    # If token is provided and invalid, reject with 1008 Policy Violation
    if token is not None and token != settings.ws_auth_token and token != "dev":
        logger.warning(f"Rejected unauthenticated WebSocket attempt: invalid token '{token}'")
        await websocket.close(code=1008)
        return

    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "handshake",
            "message": "Connected to HoneyNet Real-Time Telemetry Bus",
            "active_clients": len(ws_manager.active_connections)
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket client disconnected ({e})")
        ws_manager.disconnect(websocket)

# -----------------------------------------------------------------------------
# REST Endpoints with Strict response_model Annotations
# -----------------------------------------------------------------------------
@app.get("/", response_model=Dict[str, str])
def root():
    return {
        "service": "HoneyNet AI Adaptive Honeynet SOC Core",
        "status": "operational",
        "version": "2.2.0",
        "docs": "/docs",
        "websocket": "/ws/live"
    }

@app.get("/api/status", response_model=Dict[str, Any])
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

@app.get("/api/overview", response_model=OverviewMetrics)
def get_dashboard_overview():
    """Returns top-level SOC telemetry metrics."""
    metrics = get_overview_metrics()
    ollama_ok, _ = check_ollama_health()
    metrics.ollama_status = "Active (Native M4)" if ollama_ok else "Heuristic Engine"
    metrics.cowrie_status = "Listening (:2222)" if COWRIE_LOG_PATH.exists() else "Standby"
    return metrics

@app.get("/api/sessions", response_model=List[SessionSummary])
def list_sessions():
    """Returns all attacker sessions ordered by last activity."""
    return get_all_sessions()

@app.get("/api/sessions/{session_id}", response_model=SessionDoc)
def get_session_detail(session_id: str):
    """Returns full forensic details for a specific session."""
    session = get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.get("/api/events", response_model=List[CommandEvent])
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

@app.get("/api/attack-path", response_model=AttackPathGraph)
@app.get("/api/attack-path/", response_model=AttackPathGraph)
def get_default_attack_path():
    """Returns a baseline graph when no session is explicitly selected."""
    return build_attack_path_graph([], 0)

@app.get("/api/attack-path/{session_id}", response_model=AttackPathGraph)
def get_session_attack_path(session_id: str):
    """Constructs React Flow graph nodes and edges representing attacker lateral movement."""
    if not session_id or session_id.strip() == "":
        return build_attack_path_graph([], 0)
    session = get_session_by_id(session_id)
    if not session:
        return build_attack_path_graph([], 0)
    cats = session.categories_triggered
    risk = session.attacker_profile.risk_score
    return build_attack_path_graph(cats, risk)

@app.get("/api/mitre-matrix", response_model=List[MitreTechniqueStat])
def get_mitre_matrix():
    """Aggregates all triggered MITRE ATT&CK techniques with counts and samples."""
    return get_mitre_statistics()

@app.get("/api/assets", response_model=List[GeneratedAsset])
def list_assets():
    """Returns all dynamically generated deception assets."""
    return get_all_assets()

# -----------------------------------------------------------------------------
# Attack Simulator Trigger API (For Dashboard & Live Demos)
# -----------------------------------------------------------------------------
@app.post("/api/simulator/trigger", response_model=Dict[str, Any])
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
