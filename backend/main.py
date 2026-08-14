"""
HoneyNet FastAPI Application
Central backend orchestrator for adaptive honeypot monitoring.
"""
import threading
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import COWRIE_LOG_PATH, OLLAMA_MODEL, OLLAMA_URL
from backend.db import (
    init_db,
    get_all_sessions,
    get_events_by_session,
    get_all_events,
    get_overview_metrics,
    record_event
)
from backend.classifier import (
    check_ollama_health,
    warmup_classifier,
    classify_command,
    generate_attacker_summary
)
from backend.mitre_mapper import map_command_to_mitre
from backend.asset_manager import get_assets_for_category, seed_honeyfs_from_templates
from backend.log_tailer import CowrieLogTailer

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
    logger.info("Initializing HoneyNet SQLite WAL Database...")
    init_db()
    
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
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Request Models
class SimulateCommandRequest(BaseModel):
    session_id: str = "sim_attacker_01"
    src_ip: str = "198.51.100.42"
    command: str
    scenario: Optional[str] = None

class ClassifyRequest(BaseModel):
    command: str

@app.get("/")
def root():
    return {
        "service": "HoneyNet AI Adaptive Honeypot",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/api/status")
def get_system_status():
    """System health check including Ollama connectivity and log file status."""
    ollama_ok, ollama_msg = check_ollama_health()
    log_exists = COWRIE_LOG_PATH.exists()
    
    metrics = get_overview_metrics()
    
    return {
        "status": "online",
        "ollama": {
            "healthy": ollama_ok,
            "url": OLLAMA_URL,
            "model": OLLAMA_MODEL,
            "message": ollama_msg
        },
        "cowrie_log": {
            "path": str(COWRIE_LOG_PATH),
            "exists": log_exists,
            "size_bytes": COWRIE_LOG_PATH.stat().st_size if log_exists else 0
        },
        "metrics": metrics
    }

@app.get("/api/metrics")
def get_metrics():
    """Retrieves live aggregate threat metrics."""
    return get_overview_metrics()

@app.get("/api/sessions")
def list_sessions():
    """Returns all recorded attacker sessions sorted by latest activity."""
    return get_all_sessions()

@app.get("/api/events")
def list_events(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(100, ge=1, le=500, description="Max events to return")
):
    """Returns real-time event logs, optionally filtered by session."""
    if session_id:
        return get_events_by_session(session_id)
    return get_all_events(limit=limit)

@app.post("/api/classify")
def classify_adhoc_command(req: ClassifyRequest):
    """Ad-hoc classification for testing."""
    category, method = classify_command(req.command)
    files = get_assets_for_category(category) if category != "other" else []
    mitre_tag, mitre_name, risk_score = map_command_to_mitre(req.command, category)
    return {
        "command": req.command,
        "category": category,
        "method": method,
        "files_served": files,
        "mitre": {
            "tag": mitre_tag,
            "name": mitre_name
        },
        "risk_score": risk_score
    }

@app.post("/api/simulate")
def simulate_attack_command(req: SimulateCommandRequest):
    """
    Direct simulation endpoint: processes a synthetic attacker command through
    the full classification, asset deployment, and persistence pipeline.
    """
    category, method = classify_command(req.command)
    files_served = get_assets_for_category(category) if category != "other" else []
    mitre_tag, mitre_name, risk_score = map_command_to_mitre(req.command, category)
    
    event_id = record_event(
        session_id=req.session_id,
        src_ip=req.src_ip,
        command=req.command,
        category=category,
        files_served=files_served,
        mitre_tag=mitre_tag,
        mitre_name=mitre_name,
        event_risk_score=risk_score
    )
    
    return {
        "event_id": event_id,
        "session_id": req.session_id,
        "src_ip": req.src_ip,
        "command": req.command,
        "category": category,
        "classification_method": method,
        "files_served": files_served,
        "mitre_tag": mitre_tag,
        "mitre_name": mitre_name,
        "risk_score": risk_score
    }
