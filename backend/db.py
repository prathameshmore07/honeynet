"""
HoneyNet Database Layer
SQLite with WAL mode and busy_timeout for concurrent multi-threaded access.
"""
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
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
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                src_ip TEXT,
                start_time TEXT,
                last_active TEXT,
                total_commands INTEGER DEFAULT 0,
                categories_triggered TEXT DEFAULT '[]',
                risk_score INTEGER DEFAULT 0,
                ai_summary TEXT DEFAULT ''
            );
        """)
        
        # Events table
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
        
        # Indexes for fast lookup and dashboard streaming
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(last_active);")
        conn.commit()

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
                INSERT INTO sessions (session_id, src_ip, start_time, last_active, total_commands, categories_triggered, risk_score, ai_summary)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            """, (session_id, src_ip, now_iso, now_iso, json.dumps(cat_list), event_risk_score, ""))
        else:
            try:
                existing_cats = json.loads(session_row["categories_triggered"])
            except Exception:
                existing_cats = []
            
            if category != "other" and category not in existing_cats:
                existing_cats.append(category)
            
            new_total = session_row["total_commands"] + 1
            # Session risk score is cumulative or max of events
            current_risk = session_row["risk_score"] or 0
            new_risk = min(100, current_risk + event_risk_score if event_risk_score > 0 else current_risk + 5)
            
            cursor.execute("""
                UPDATE sessions
                SET last_active = ?, total_commands = ?, categories_triggered = ?, risk_score = ?
                WHERE session_id = ?
            """, (now_iso, new_total, json.dumps(existing_cats), new_risk, session_id))
            
        conn.commit()
        return event_id

def update_session_summary(session_id: str, summary: str) -> None:
    """Updates the AI summary for a session."""
    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET ai_summary = ? WHERE session_id = ?", (summary, session_id))
        conn.commit()

def get_all_sessions() -> List[Dict[str, Any]]:
    """Retrieves all sessions ordered by most recent activity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY last_active DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_events_by_session(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves all events for a given session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_all_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves the latest events across all sessions."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_overview_metrics() -> Dict[str, Any]:
    """Retrieves aggregate metrics for the dashboard."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total_sessions FROM sessions")
        total_sessions = cursor.fetchone()["total_sessions"]
        
        cursor.execute("SELECT COUNT(*) as total_events FROM events")
        total_events = cursor.fetchone()["total_events"]
        
        cursor.execute("SELECT COUNT(*) as total_assets FROM events WHERE category != 'other'")
        total_assets_served = cursor.fetchone()["total_assets"]
        
        cursor.execute("SELECT AVG(risk_score) as avg_risk FROM sessions")
        avg_risk = cursor.fetchone()["avg_risk"] or 0
        
        return {
            "total_sessions": total_sessions,
            "total_events": total_events,
            "total_assets_served": total_assets_served,
            "avg_risk": round(avg_risk, 1)
        }
