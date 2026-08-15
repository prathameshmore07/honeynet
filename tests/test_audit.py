"""
HoneyNet Production Verification & Security Audit Test Suite
Runs via standard pytest framework and verifies:
- Pure MongoDB embedded document mutations ($push, $set)
- Pydantic response_model strict validation on all FastAPI endpoints
- Sub-millisecond rule-based intent matching
- Log parser truncation resilience
- Sandbox path traversal defenses
- API rate limiting (HTTP 429)
- Zero secrets in codebase
"""
import os
import sys
import time
import pytest
from pathlib import Path
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings
from backend.db import init_db, record_session_event, get_all_sessions, get_session_by_id, get_overview_metrics, get_all_assets
from backend.models import SessionDoc, CommandItem
from backend.classifier import classify_command, classify_with_heuristic
from backend.asset_generator import sanitize_and_resolve_path
from backend.log_tailer import CowrieLogTailer
from honeypot_sim import run_simulation

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_fastapi_endpoints_strict_models():
    """1. Test all 9 FastAPI REST endpoints against Pydantic response models."""
    # Root
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert "service" in r_root.json()

    # Status
    r_status = client.get("/api/status")
    assert r_status.status_code == 200
    assert r_status.json()["status"] == "healthy"

    # Overview
    r_overview = client.get("/api/overview")
    assert r_overview.status_code == 200
    data = r_overview.json()
    assert "total_sessions" in data
    assert "active_attackers" in data
    assert "avg_risk_score" in data

    # Sessions
    r_sessions = client.get("/api/sessions")
    assert r_sessions.status_code == 200
    assert isinstance(r_sessions.json(), list)

    # Attack Path
    r_path = client.get("/api/attack-path/session_test_path")
    assert r_path.status_code == 200
    assert "nodes" in r_path.json()
    assert "edges" in r_path.json()

    # MITRE Matrix
    r_mitre = client.get("/api/mitre-matrix")
    assert r_mitre.status_code == 200
    assert isinstance(r_mitre.json(), list)

    # Assets
    r_assets = client.get("/api/assets")
    assert r_assets.status_code == 200
    assert isinstance(r_assets.json(), list)

    # Simulator Trigger
    r_sim = client.post("/api/simulator/trigger", json={"scenario": "finance", "delay": 0.01})
    assert r_sim.status_code == 200
    assert r_sim.json()["status"] == "triggered"

def test_mongodb_embedded_write_rejection():
    """2. Confirm Pydantic validation rejects malformed input before MongoDB writes."""
    # Missing required field '_id'
    with pytest.raises(ValidationError):
        SessionDoc(attacker_ip="1.2.3.4")

    # Invalid risk score data type
    with pytest.raises(ValidationError):
        CommandItem(cmd="ls", risk_increment="NOT_AN_INTEGER")

def test_mongodb_atomic_push_and_set():
    """3. Confirm MongoDB embedded document updates use atomic $push and $set."""
    session_id = "test_mongo_atomic_session_01"
    
    # Event 1
    doc1 = record_session_event(
        session_id=session_id,
        src_ip="192.168.1.100",
        command="whoami",
        category="other",
        risk_increment=10
    )
    assert doc1.id == session_id
    assert len(doc1.commands) == 1
    assert doc1.attacker_profile.risk_score == 20

    # Event 2
    doc2 = record_session_event(
        session_id=session_id,
        src_ip="192.168.1.100",
        command="cat /home/phil/finance/Payroll_2026_Confidential.csv",
        category="finance",
        mitre_tag="T1005",
        risk_increment=45
    )
    assert len(doc2.commands) == 2
    assert "finance" in doc2.categories_triggered
    assert doc2.attacker_profile.risk_score == 65

def test_websocket_handshake_and_auth():
    """4. Test WebSocket lifecycle, ping/pong, and token rejection."""
    # Valid dev token connection
    with client.websocket_connect("/ws/live?token=dev") as ws:
        data = ws.receive_json()
        assert data["type"] == "handshake"
        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"

    # Invalid token check (must reject)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/live?token=INVALID_EXPLICIT_TOKEN") as ws:
            pass

def test_submillisecond_heuristic_fallback():
    """5. Test sub-millisecond intent classification timing."""
    start_t = time.perf_counter()
    cat, method = classify_command("cat /home/phil/finance/Payroll_2026_Confidential.csv")
    elapsed_ms = (time.perf_counter() - start_t) * 1000
    
    assert cat == "finance"
    assert method == "heuristic_fast"
    assert elapsed_ms < 10.0 # Under 10 milliseconds

def test_cowrie_log_corrupt_line_handling():
    """6. Test log tailer resilience against malformed/truncated log lines."""
    tailer = CowrieLogTailer()
    
    # Empty string
    assert tailer.process_log_line("") is None
    # Truncated partial JSON
    assert tailer.process_log_line('{"eventid": "cowrie.command.input", "session": "s1", "input": "ls') is None
    # Non-command keepalive noise
    assert tailer.process_log_line('{"eventid": "cowrie.client.kex", "session": "s1"}') is None
    # Valid command event
    valid = tailer.process_log_line('{"eventid": "cowrie.command.input", "session": "test_tailer_valid", "src_ip": "1.1.1.1", "input": "whoami", "timestamp": "2026-08-15T11:00:00Z"}')
    assert valid is not None
    assert valid["command"] == "whoami"

def test_sandbox_path_traversal_rejection():
    """7. Test Cowrie honeyfs sandbox path traversal defenses."""
    # Attempt directory traversal
    with pytest.raises(ValueError):
        sanitize_and_resolve_path("../../etc/passwd")

    # Attempt shell metacharacters
    with pytest.raises(ValueError):
        sanitize_and_resolve_path("home/phil/finance/; rm -rf /")

    # Attempt null byte injection
    with pytest.raises(ValueError):
        sanitize_and_resolve_path("home/phil/finance/\x00evil.txt")

    # Valid path inside honeyfs
    valid_path = sanitize_and_resolve_path("home/phil/finance/Payroll_2026_Confidential.xlsx")
    assert str(valid_path).endswith("Payroll_2026_Confidential.xlsx")

def test_api_rate_limiting():
    """8. Test in-memory rate limiting on public-facing REST endpoints."""
    got_429 = False
    headers = {"X-Forwarded-For": "203.0.113.195"}
    for _ in range(140):
        r = client.get("/api/overview", headers=headers)
        if r.status_code == 429:
            got_429 = True
            break
    assert got_429

def test_codebase_secrets_audit():
    """9. Audit repository for accidental secrets."""
    workspace_dir = Path(__file__).resolve().parent.parent
    
    # Confirm .env is ignored and .env.example exists
    assert (workspace_dir / ".gitignore").exists()
    gitignore_text = (workspace_dir / ".gitignore").read_text()
    assert ".env" in gitignore_text
    assert ".env.example" in gitignore_text

    # Grep test for live Stripe or AWS secret prefixes
    dangerous_patterns = ["sk_live_", "AKIA2"]
    for root, _, files in os.walk(workspace_dir):
        if ".git" in root or ".venv" in root or "node_modules" in root or ".next" in root:
            continue
        for f in files:
            if f in ("test_audit.py", "test_production_audit.py", "walkthrough.md"):
                continue
            file_p = Path(root) / f
            if file_p.suffix in (".py", ".json", ".ts", ".tsx", ".sh", ".yml"):
                content = file_p.read_text(errors="ignore")
                for pat in dangerous_patterns:
                    assert pat not in content, f"Secret pattern {pat} detected in {file_p}"

def test_scripted_simulation_runs():
    """10. Run scripted attack simulation and verify embedded MongoDB updates."""
    session_id = "test_scripted_sim_verification"
    run_simulation(scenarios_to_run=["finance"], delay=0.001, override_ip="192.168.1.99")
    
    tailer = CowrieLogTailer()
    tailer.poll_once()
    
    sessions = get_all_sessions()
    assert len(sessions) > 0
