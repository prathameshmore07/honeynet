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
from backend.db import record_session_event, get_session_by_id
from backend.classifier import classify_command
from backend.mitre_mapper import map_command_to_mitre
from backend.asset_generator import generate_dynamic_deception_assets
from backend.identity_seeder import generate_company_identity
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

        # 1. AI Intent Classification (Instant Heuristic + Ollama fallback)
        category, method = classify_command(command)

        # 2. Company Identity & Dynamic Asset Deployment
        existing_session = get_session_by_id(session_id)
        company = existing_session.company_identity if (existing_session and existing_session.company_identity) else generate_company_identity(session_id)

        deployed_assets = []
        if category in ("finance", "git", "aws", "hr", "database"):
            already_provisioned = existing_session is not None and category in existing_session.categories_triggered
            if not already_provisioned:
                deployed_assets = generate_dynamic_deception_assets(category, session_id, company)

        # 3. MITRE ATT&CK Mapping & Risk Scoring
        mitre_tag, mitre_name, risk_score = map_command_to_mitre(command, category)
        files_served = [a.get("path", "") for a in deployed_assets]

        # 4. Database Persistence (MongoDB Embedded Document Engine)
        session_doc = record_session_event(
            session_id=session_id,
            src_ip=src_ip,
            command=command,
            category=category,
            classification_method=method,
            mitre_tag=mitre_tag,
            mitre_name=mitre_name,
            risk_increment=risk_score,
            new_assets=deployed_assets
        )

        event_payload = {
            "session_id": session_id,
            "src_ip": src_ip,
            "command": command,
            "category": category,
            "classification_method": method,
            "files_served": files_served,
            "mitre_tag": mitre_tag,
            "mitre_name": mitre_name,
            "event_risk_score": risk_score,
            "session_risk_score": session_doc.attacker_profile.risk_score if session_doc else risk_score,
            "skill_level": session_doc.attacker_profile.skill_level if session_doc else "Opportunistic",
            "inferred_intent": category.capitalize() if category != "other" else "Reconnaissance",
            "timestamp": timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # 5. Real-time WebSocket Broadcast
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
            f"MITRE: {mitre_tag} | Deployed: {len(deployed_assets)} | Risk: {event_payload['session_risk_score']}"
        )

        return event_payload

    def poll_once(self) -> int:
        """Polls log file once, processing any new appended lines."""
        if not self.log_path.exists():
            return 0

        processed = 0
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.file_pos)
                for line in f:
                    if self.process_log_line(line):
                        processed += 1
                self.file_pos = f.tell()
        except Exception as e:
            logger.error(f"Error reading log file {self.log_path}: {e}")
        return processed

    def run_loop(self, poll_interval: float = 0.5):
        """Continuously tails the Cowrie log file in a background worker loop."""
        self.running = True
        logger.info(f"HoneyNet Cowrie Log Tailer started (watching {self.log_path})...")

        # Fast-forward to end of file on startup unless empty
        if self.log_path.exists():
            self.file_pos = self.log_path.stat().st_size

        while self.running:
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Tailer worker loop exception: {e}")
            time.sleep(poll_interval)

    def stop(self):
        """Stops the tailer worker loop."""
        self.running = False
