"""
HoneyNet Cowrie Log Tailer
Tails cowrie.json in real time, filters command events, deduplicates,
classifies intent with AI/heuristics, deploys synthetic assets, updates attacker profiles,
and broadcasts live telemetry to connected WebSocket clients.
"""
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Set

from backend.config import COWRIE_LOG_PATH
from backend.db import record_event, update_session_profile, get_events_by_session, get_session_by_id
from backend.classifier import classify_command
from backend.mitre_mapper import map_command_to_mitre
from backend.asset_generator import generate_assets_for_intent
from backend.profiler import evaluate_attacker_profile
from backend.ws_manager import broadcast_sync

logger = logging.getLogger("honeynet.tailer")

class CowrieLogTailer:
    """Monitors and processes Cowrie JSON logs."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = Path(log_path) if log_path else COWRIE_LOG_PATH
        self.file_pos = 0
        self.running = False
        # Sliding window deduplication set: stores (session_id, command, time_bucket)
        self.seen_events: Set[str] = set()
        self.session_cmd_counts: Dict[str, int] = {}

    def _get_time_bucket(self, timestamp_str: str) -> int:
        """Derives a coarse 3-second time bucket for event deduplication."""
        try:
            return int(time.time()) // 3
        except Exception:
            return int(time.time()) // 3

    def process_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parses a single JSON line from cowrie.json.
        Filters strictly for eventid == 'cowrie.command.input' and deduplicates.
        """
        line = line.strip()
        if not line:
            return None

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None

        event_id = data.get("eventid", "")
        # Strict filtering: ignore keepalive and connection noise
        if event_id != "cowrie.command.input":
            return None

        session_id = data.get("session", "unknown_session")
        src_ip = data.get("src_ip", "127.0.0.1")
        command = data.get("input", "").strip()
        timestamp = data.get("timestamp", "")

        if not command:
            return None

        # Deduplication check (session_id + command + 3-sec window)
        time_bucket = self._get_time_bucket(timestamp)
        dedupe_key = f"{session_id}::{command}::{time_bucket}"

        if dedupe_key in self.seen_events:
            logger.debug(f"Duplicate command skipped: {dedupe_key}")
            return None

        self.seen_events.add(dedupe_key)
        if len(self.seen_events) > 2000:
            self.seen_events = set(list(self.seen_events)[-1000:])

        # 1. AI Intent Classification (Heuristic + Ollama)
        category, method = classify_command(command)

        # 2. Dynamic Asset Deployment (if targeted category)
        deployed_assets = []
        if category != "other":
            deployed_assets = generate_assets_for_intent(session_id, category)

        # 3. MITRE ATT&CK Mapping & Risk Scoring
        mitre_tag, mitre_name, risk_score = map_command_to_mitre(command, category)
        files_served = [a.get("file_path", "") for a in deployed_assets]

        # 4. Database Persistence
        db_id = record_event(
            session_id=session_id,
            src_ip=src_ip,
            command=command,
            category=category,
            files_served=files_served,
            mitre_tag=mitre_tag,
            mitre_name=mitre_name,
            event_risk_score=risk_score,
            timestamp=timestamp
        )

        # 5. Attacker Profiling Update
        all_session_events = get_events_by_session(session_id)
        session_data = get_session_by_id(session_id) or {}
        categories_triggered = session_data.get("categories_triggered", [])
        current_risk = session_data.get("risk_score", risk_score)

        profile = evaluate_attacker_profile(all_session_events, categories_triggered, current_risk)
        update_session_profile(
            session_id=session_id,
            inferred_intent=profile["inferred_intent"],
            skill_level=profile["skill_level"],
            goal_summary=profile["goal_summary"],
            ai_summary=profile["ai_summary"],
            risk_score=profile["risk_score"]
        )

        event_payload = {
            "id": db_id,
            "session_id": session_id,
            "src_ip": src_ip,
            "command": command,
            "category": category,
            "classification_method": method,
            "files_served": files_served,
            "mitre_tag": mitre_tag,
            "mitre_name": mitre_name,
            "event_risk_score": risk_score,
            "session_risk_score": profile["risk_score"],
            "skill_level": profile["skill_level"],
            "inferred_intent": profile["inferred_intent"],
            "timestamp": timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # 6. Real-time WebSocket Broadcast
        broadcast_sync({
            "type": "command_event",
            "data": event_payload
        })

        if deployed_assets:
            broadcast_sync({
                "type": "asset_created",
                "data": {
                    "session_id": session_id,
                    "category": category,
                    "assets": deployed_assets
                }
            })

        logger.info(
            f"[{session_id[:8]}] '{command}' -> Cat: {category} ({method}) | "
            f"MITRE: {mitre_tag} | Deployed: {len(deployed_assets)} | Risk: {profile['risk_score']}"
        )

        return event_payload

    def poll_once(self) -> int:
        """Reads and processes any newly appended lines in cowrie.json."""
        if not self.log_path.exists():
            return 0

        processed = 0
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.file_pos)
                for line in f:
                    res = self.process_log_line(line)
                    if res:
                        processed += 1
                self.file_pos = f.tell()
        except Exception as e:
            logger.error(f"Error reading log file {self.log_path}: {e}")

        return processed

    def run_loop(self, poll_interval: float = 0.5):
        """Continuous polling loop for log tailing."""
        self.running = True
        logger.info(f"Started Cowrie log tailer on {self.log_path}")
        while self.running:
            self.poll_once()
            time.sleep(poll_interval)

    def stop(self):
        """Stops the polling loop."""
        self.running = False
