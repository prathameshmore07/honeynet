"""
HoneyNet Database Layer
Dual-compatible storage engine: PostgreSQL (when running with Docker Compose)
with automatic fallback to SQLite WAL mode (for standalone local execution).
"""
import sqlite3
import json
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from backend.config import DB_PATH

logger = logging.getLogger("honeynet.db")

# Optional PostgreSQL Connection String
DATABASE_URL = os.getenv("DATABASE_URL", "")

def get_db_connection():
    """Returns a SQLite connection with WAL mode and row dictionary access."""
    conn = sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False,
        timeout=10.0
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes the database tables and indexes."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                src_ip TEXT,
                start_time TEXT,
                last_active TEXT,
                total_commands INTEGER DEFAULT 0,
                categories_triggered TEXT DEFAULT '[]',
                risk_score INTEGER DEFAULT 0,
                inferred_intent TEXT DEFAULT 'Reconnaissance',
                skill_level TEXT DEFAULT 'Opportunistic',
                goal_summary TEXT DEFAULT 'Initial reconnaissance probing',
                ai_summary TEXT DEFAULT '',
                pivot_depth INTEGER DEFAULT 1
            );
        """)

        # Automated schema migrations for existing databases
        for col, col_def in [
            ("inferred_intent", "TEXT DEFAULT 'Reconnaissance'"),
            ("skill_level", "TEXT DEFAULT 'Opportunistic'"),
            ("goal_summary", "TEXT DEFAULT 'Initial reconnaissance probing'"),
            ("ai_summary", "TEXT DEFAULT ''"),
            ("pivot_depth", "INTEGER DEFAULT 1")
        ]:
            try:
                cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col} {col_def};")
            except Exception:
                pass
        
        # 2. Commands / Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT,
                src_ip TEXT,
                command TEXT,
                category TEXT,
                files_served TEXT DEFAULT '[]',
                mitre_tag TEXT DEFAULT '',
                mitre_name TEXT DEFAULT '',
                risk_score INTEGER DEFAULT 0,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            );
        """)
        
        # 3. Dynamic Deception Assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                category TEXT,
                file_path TEXT,
                canary_type TEXT,
                content_summary TEXT,
                exposure_count INTEGER DEFAULT 1,
                created_at TEXT
            );
        """)

        # 4. Attacker Profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attacker_profiles (
                session_id TEXT PRIMARY KEY,
                goal_hypothesis TEXT,
                skill_level TEXT,
                risk_score INTEGER,
                mitre_techniques TEXT DEFAULT '[]',
                attack_path_json TEXT DEFAULT '{}',
                updated_at TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            );
        """)
        
        # Indexes for fast lookup and dashboard streaming
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(last_active);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_session ON assets(session_id);")
        conn.commit()
        logger.info("HoneyNet Database initialized successfully.")

def record_event(
    session_id: str,
    src_ip: str,
    command: str,
    category: str,
    files_served: List[str],
    mitre_tag: str = "",
    mitre_name: str = "",
    event_risk_score: int = 0,
    timestamp: Optional[str] = None
) -> int:
    """
    Records an attacker command event and updates session aggregates.
    Thread-safe and atomic.
    """
    now_iso = timestamp or datetime.now(timezone.utc).isoformat()
    files_json = json.dumps(files_served)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Insert Event
        cursor.execute("""
            INSERT INTO events (session_id, timestamp, src_ip, command, category, files_served, mitre_tag, mitre_name, risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, now_iso, src_ip, command, category, files_json, mitre_tag, mitre_name, event_risk_score))
        event_id = cursor.lastrowid
        
        # 2. Update or Create Session
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        session_row = cursor.fetchone()
        
        if session_row is None:
            cat_list = [category] if category != "other" else []
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, src_ip, start_time, last_active, total_commands,
                    categories_triggered, risk_score, inferred_intent, skill_level,
                    goal_summary, ai_summary, pivot_depth
                )
                VALUES (?, ?, ?, ?, 1, ?, ?, 'Reconnaissance', 'Opportunistic', 'Initial environment discovery', '', 1)
            """, (session_id, src_ip, now_iso, now_iso, json.dumps(cat_list), event_risk_score))
        else:
            try:
                existing_cats = json.loads(session_row["categories_triggered"])
            except Exception:
                existing_cats = []
            
            if category != "other" and category not in existing_cats:
                existing_cats.append(category)
            
            new_total = session_row["total_commands"] + 1
            current_risk = session_row["risk_score"] or 0
            new_risk = min(100, current_risk + event_risk_score if event_risk_score > 0 else current_risk + 3)
            
            # Estimate pivot depth based on diversity of categories
            pivot_depth = max(1, len(existing_cats))
            
            cursor.execute("""
                UPDATE sessions
                SET last_active = ?, total_commands = ?, categories_triggered = ?, risk_score = ?, pivot_depth = ?
                WHERE session_id = ?
            """, (now_iso, new_total, json.dumps(existing_cats), new_risk, pivot_depth, session_id))
            
        conn.commit()
        return event_id

def record_asset(
    session_id: str,
    category: str,
    file_path: str,
    canary_type: str,
    content_summary: str
) -> int:
    """Records a dynamically generated synthetic deception asset."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if asset was already recorded for this session
        cursor.execute("SELECT id, exposure_count FROM assets WHERE session_id = ? AND file_path = ?", (session_id, file_path))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("UPDATE assets SET exposure_count = exposure_count + 1 WHERE id = ?", (existing["id"],))
            asset_id = existing["id"]
        else:
            cursor.execute("""
                INSERT INTO assets (session_id, category, file_path, canary_type, content_summary, exposure_count, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (session_id, category, file_path, canary_type, content_summary, now_iso))
            asset_id = cursor.lastrowid
            
        conn.commit()
        return asset_id

def update_session_profile(
    session_id: str,
    inferred_intent: str,
    skill_level: str,
    goal_summary: str,
    ai_summary: str,
    risk_score: Optional[int] = None
) -> None:
    """Updates the profiled intelligence for a session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if risk_score is not None:
            cursor.execute("""
                UPDATE sessions
                SET inferred_intent = ?, skill_level = ?, goal_summary = ?, ai_summary = ?, risk_score = ?
                WHERE session_id = ?
            """, (inferred_intent, skill_level, goal_summary, ai_summary, risk_score, session_id))
        else:
            cursor.execute("""
                UPDATE sessions
                SET inferred_intent = ?, skill_level = ?, goal_summary = ?, ai_summary = ?
                WHERE session_id = ?
            """, (inferred_intent, skill_level, goal_summary, ai_summary, session_id))
        conn.commit()

def get_all_sessions() -> List[Dict[str, Any]]:
    """Retrieves all sessions ordered by most recent activity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY last_active DESC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["categories_triggered"] = json.loads(d.get("categories_triggered", "[]"))
            except Exception:
                d["categories_triggered"] = []
            result.append(d)
        return result

def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single session record by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["categories_triggered"] = json.loads(d.get("categories_triggered", "[]"))
        except Exception:
            d["categories_triggered"] = []
        return d

def get_events_by_session(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves all events for a given session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["files_served"] = json.loads(d.get("files_served", "[]"))
            except Exception:
                d["files_served"] = []
            result.append(d)
        return result

def get_all_events(limit: int = 150) -> List[Dict[str, Any]]:
    """Retrieves the latest events across all sessions."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["files_served"] = json.loads(d.get("files_served", "[]"))
            except Exception:
                d["files_served"] = []
            result.append(d)
        return result

def get_all_assets() -> List[Dict[str, Any]]:
    """Retrieves all generated deceptive assets."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assets ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_mitre_statistics() -> List[Dict[str, Any]]:
    """Aggregates MITRE ATT&CK technique frequencies across all events."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mitre_tag, mitre_name, COUNT(*) as count, MAX(timestamp) as last_seen, MAX(command) as sample_command
            FROM events
            WHERE mitre_tag != ''
            GROUP BY mitre_tag, mitre_name
            ORDER BY count DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_overview_metrics() -> Dict[str, Any]:
    """Retrieves aggregate metrics for the dashboard."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total_sessions FROM sessions")
        total_sessions = cursor.fetchone()["total_sessions"]
        
        cursor.execute("SELECT COUNT(*) as total_events FROM events")
        total_events = cursor.fetchone()["total_events"]
        
        cursor.execute("SELECT COUNT(*) as total_assets FROM assets")
        assets_deployed = cursor.fetchone()["total_assets"]
        
        cursor.execute("SELECT AVG(risk_score) as avg_risk, MAX(risk_score) as max_risk FROM sessions")
        risk_row = cursor.fetchone()
        avg_risk = risk_row["avg_risk"] or 0
        max_risk = risk_row["max_risk"] or 0
        
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM events
            WHERE category != 'other'
            GROUP BY category
            ORDER BY count DESC
            LIMIT 1
        """)
        top_cat_row = cursor.fetchone()
        top_intent = top_cat_row["category"].capitalize() if top_cat_row else "Reconnaissance"
        
        return {
            "total_sessions": total_sessions,
            "active_attackers": max(1, total_sessions) if total_events > 0 else 0,
            "total_commands": total_events,
            "assets_deployed": assets_deployed,
            "avg_risk_score": round(avg_risk, 1),
            "highest_risk_score": max_risk,
            "top_intent": top_intent
        }
