"""
HoneyNet Cowrie Log Tailer
Tails cowrie.json in real time, filters command events, deduplicates,
classifies intent with AI/heuristics, and persists forensic records to SQLite.
"""
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Set
from backend.config import COWRIE_LOG_PATH
from backend.db import record_event, update_session_summary, get_events_by_session
from backend.classifier import classify_command, generate_attacker_summary
from backend.mitre_mapper import map_command_to_mitre
from backend.asset_manager import get_assets_for_category

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
            # Fallback to current time if parsing fails
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
        # Strict filtering: ignore login, connect, fingerprint, keepalive noise
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
        # Keep deduplication cache bounded
        if len(self.seen_events) > 2000:
            self.seen_events = set(list(self.seen_events)[-1000:])

        # 1. AI Intent Classification
        category, method = classify_command(command)

        # 2. Asset Discovery & Deployment Mapping
        files_served = get_assets_for_category(category) if category != "other" else []

        # 3. MITRE ATT&CK Mapping & Risk Scoring
        mitre_tag, mitre_name, risk_score = map_command_to_mitre(command, category)

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

        # Update running session command count & trigger periodic summary update
        current_cnt = self.session_cmd_counts.get(session_id, 0) + 1
        self.session_cmd_counts[session_id] = current_cnt

        if current_cnt % 3 == 0 or category != "other":
            # Generate updated AI synopsis
            events = get_events_by_session(session_id)
            cmds = [e["command"] for e in events if e.get("command")]
            summary = generate_attacker_summary(cmds)
            update_session_summary(session_id, summary)

        logger.info(
            f"[{session_id[:8]}] Cmd: '{command}' -> Cat: {category} ({method}) | "
            f"MITRE: {mitre_tag} | Assets: {len(files_served)}"
        )

        return {
            "id": db_id,
            "session_id": session_id,
            "src_ip": src_ip,
            "command": command,
            "category": category,
            "files_served": files_served,
            "mitre_tag": mitre_tag,
            "mitre_name": mitre_name,
            "risk_score": risk_score
        }

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
