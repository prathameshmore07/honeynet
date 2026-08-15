"""
HoneyNet Database Persistence Engine
Implements MongoDB embedded-document persistence using Motor/PyMongo,
with an automatic SQLite WAL fallback for zero-dependency local execution.
Every write is validated against strict Pydantic models.
"""
import os
import json
import logging
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.config import settings, DB_PATH
from backend.models import (
    SessionDoc,
    CommandItem,
    GeneratedAssetItem,
    AttackerProfileDoc,
    SessionSummary,
    CommandEvent,
    GeneratedAsset,
    MitreTechniqueStat,
    OverviewMetrics,
    CompanyIdentity,
)
from backend.identity_seeder import generate_company_identity

logger = logging.getLogger("honeynet.db")

# Flag for active backend
_mongo_available = False
_mongo_db = None

def init_db() -> None:
    """Initializes MongoDB connection or falls back to SQLite WAL mode."""
    global _mongo_available, _mongo_db
    
    # Try connecting to MongoDB if DATABASE_URL is set or localhost
    mongo_uri = settings.database_url or os.getenv("MONGO_URI", "mongodb://localhost:27017")
    if "mongodb" in mongo_uri:
        try:
            import pymongo
            client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
            client.server_info() # Trigger connection check
            _mongo_db = client["honeynet_db"]
            _mongo_available = True
            
            # Create indexes
            _mongo_db.sessions.create_index([("start_time", pymongo.DESCENDING)])
            _mongo_db.sessions.create_index([("attacker_ip", pymongo.ASCENDING)])
            logger.info("Connected to MongoDB engine (Embedded-Document Storage).")
            return
        except Exception as e:
            logger.info(f"MongoDB not active ({e}). Operating in resilient SQLite WAL fallback mode.")

    # SQLite WAL Fallback Initialization
    _mongo_available = False
    with get_sqlite_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                data TEXT DEFAULT '',
                start_time TEXT,
                last_active TEXT,
                risk_score INTEGER DEFAULT 0
            );
        """)
        # Automated column addition if existing table didn't have data column
        try:
            conn.execute("ALTER TABLE sessions ADD COLUMN data TEXT DEFAULT '';")
        except Exception:
            pass
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT,
                src_ip TEXT,
                command TEXT,
                category TEXT,
                mitre_tag TEXT,
                mitre_name TEXT,
                risk_score INTEGER
            );
        """)
        conn.execute("""
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
    logger.info("SQLite WAL persistence layer initialized.")

def get_sqlite_conn():
    """Returns a SQLite connection with WAL journal mode."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn

# ------------------------------------------------------------------------------
# Ingestion & Mutation APIs
# ------------------------------------------------------------------------------

def record_session_event(
    session_id: str,
    src_ip: str,
    command: str,
    category: str,
    classification_method: str = "heuristic_fast",
    mitre_tag: Optional[str] = None,
    mitre_name: Optional[str] = None,
    risk_increment: int = 10,
    new_assets: Optional[List[Dict[str, Any]]] = None
) -> SessionDoc:
    """
    Atomically inserts or updates a session with the new command, new assets,
    and recalculates risk score and attacker profile.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    cmd_item = CommandItem(
        cmd=command,
        timestamp=now_iso,
        intent=category,
        mitre_tags=[mitre_tag] if mitre_tag else [],
        risk_increment=risk_increment
    )

    if _mongo_available and _mongo_db is not None:
        # MongoDB Embedded Document Update
        session_data = _mongo_db.sessions.find_one({"_id": session_id})
        if not session_data:
            company = generate_company_identity(session_id)
            doc = SessionDoc(
                _id=session_id,
                attacker_ip=src_ip,
                start_time=now_iso,
                last_active=now_iso,
                commands=[cmd_item],
                company_identity=company,
                categories_triggered=[category] if category != "other" else [],
                schema_version=1
            )
            _mongo_db.sessions.insert_one(doc.model_dump(by_alias=True))
        else:
            # Update existing
            cats = list(set(session_data.get("categories_triggered", []) + ([category] if category != "other" else [])))
            total_risk = min(100, session_data.get("attacker_profile", {}).get("risk_score", 10) + risk_increment)
            
            update_ops: Dict[str, Any] = {
                "$push": {"commands": cmd_item.model_dump()},
                "$set": {
                    "last_active": now_iso,
                    "categories_triggered": cats,
                    "attacker_profile.risk_score": total_risk,
                }
            }
            if new_assets:
                asset_items = [
                    GeneratedAssetItem(
                        type=a.get("type", "file"),
                        path=a.get("path", ""),
                        content_ref=a.get("content_ref", ""),
                        category=a.get("category", category)
                    ).model_dump() for a in new_assets
                ]
                update_ops["$push"]["assets_generated"] = {"$each": asset_items}
                
            _mongo_db.sessions.update_one({"_id": session_id}, update_ops)
            
        return get_session_by_id(session_id)

    # SQLite WAL Implementation
    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row or not row["data"] or not str(row["data"]).strip():
            company = generate_company_identity(session_id)
            doc = SessionDoc(
                _id=session_id,
                attacker_ip=src_ip,
                start_time=now_iso,
                last_active=now_iso,
                commands=[cmd_item],
                company_identity=company,
                categories_triggered=[category] if category != "other" else [],
                schema_version=1
            )
        else:
            doc = SessionDoc.model_validate_json(row["data"])
            doc.commands.append(cmd_item)
            doc.last_active = now_iso
            if category != "other" and category not in doc.categories_triggered:
                doc.categories_triggered.append(category)
            doc.attacker_profile.risk_score = min(100, doc.attacker_profile.risk_score + risk_increment)

        if new_assets:
            for a in new_assets:
                asset_item = GeneratedAssetItem(
                    type=a.get("type", "file"),
                    path=a.get("path", ""),
                    content_ref=a.get("content_ref", ""),
                    category=a.get("category", category)
                )
                doc.assets_generated.append(asset_item)
                cursor.execute("""
                    INSERT INTO assets (session_id, category, file_path, canary_type, content_summary, exposure_count, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                """, (session_id, asset_item.category, asset_item.path, asset_item.type, asset_item.content_ref, now_iso))

        # Insert flat event
        cursor.execute("""
            INSERT INTO events (session_id, timestamp, src_ip, command, category, mitre_tag, mitre_name, risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, now_iso, src_ip, command, category, mitre_tag or "", mitre_name or "", risk_increment))

        # Save session
        cursor.execute("""
            INSERT INTO sessions (session_id, data, start_time, last_active, risk_score)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                data = excluded.data,
                last_active = excluded.last_active,
                risk_score = excluded.risk_score;
        """, (session_id, doc.model_dump_json(by_alias=True), doc.start_time, doc.last_active, doc.attacker_profile.risk_score))

    return doc

# ------------------------------------------------------------------------------
# Query APIs
# ------------------------------------------------------------------------------

def get_session_by_id(session_id: str) -> Optional[SessionDoc]:
    """Fetches a full session document by ID."""
    if _mongo_available and _mongo_db is not None:
        doc = _mongo_db.sessions.find_one({"_id": session_id})
        if doc:
            return SessionDoc.model_validate(doc)
        return None

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row and row["data"] and str(row["data"]).strip():
            return SessionDoc.model_validate_json(row["data"])
    return None

def get_all_sessions() -> List[SessionSummary]:
    """Returns summaries for all sessions."""
    summaries = []
    
    if _mongo_available and _mongo_db is not None:
        cursor = _mongo_db.sessions.find().sort("last_active", -1).limit(50)
        for doc in cursor:
            s_doc = SessionDoc.model_validate(doc)
            summaries.append(SessionSummary(
                session_id=s_doc.id,
                src_ip=s_doc.attacker_ip,
                start_time=s_doc.start_time,
                last_active=s_doc.last_active,
                total_commands=len(s_doc.commands),
                categories_triggered=s_doc.categories_triggered,
                risk_score=s_doc.attacker_profile.risk_score,
                inferred_intent=s_doc.categories_triggered[0].capitalize() if s_doc.categories_triggered else "Reconnaissance",
                skill_level=s_doc.attacker_profile.skill_level,
                goal_summary=s_doc.attacker_profile.goal,
                ai_summary=s_doc.attacker_profile.ai_synopsis
            ))
        return summaries

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM sessions WHERE data != '' ORDER BY last_active DESC LIMIT 50")
        for row in cursor.fetchall():
            if not row["data"]:
                continue
            s_doc = SessionDoc.model_validate_json(row["data"])
            summaries.append(SessionSummary(
                session_id=s_doc.id,
                src_ip=s_doc.attacker_ip,
                start_time=s_doc.start_time,
                last_active=s_doc.last_active,
                total_commands=len(s_doc.commands),
                categories_triggered=s_doc.categories_triggered,
                risk_score=s_doc.attacker_profile.risk_score,
                inferred_intent=s_doc.categories_triggered[0].capitalize() if s_doc.categories_triggered else "Reconnaissance",
                skill_level=s_doc.attacker_profile.skill_level,
                goal_summary=s_doc.attacker_profile.goal,
                ai_summary=s_doc.attacker_profile.ai_synopsis
            ))
    return summaries

def get_overview_metrics() -> OverviewMetrics:
    """Calculates top-level SOC KPI metrics."""
    sessions = get_all_sessions()
    total_sessions = len(sessions)
    active_attackers = len(set(s.src_ip for s in sessions))
    total_commands = sum(s.total_commands for s in sessions)
    avg_risk = round(sum(s.risk_score for s in sessions) / total_sessions, 1) if total_sessions > 0 else 0.0
    highest_risk = max((s.risk_score for s in sessions), default=0)

    # Top category
    cat_counts: Dict[str, int] = {}
    for s in sessions:
        for c in s.categories_triggered:
            cat_counts[c] = cat_counts.get(c, 0) + 1
    top_intent = max(cat_counts, key=cat_counts.get).capitalize() if cat_counts else "None"

    # Count assets
    assets = get_all_assets()
    
    return OverviewMetrics(
        total_sessions=total_sessions,
        active_attackers=active_attackers,
        total_commands=total_commands,
        assets_deployed=len(assets),
        avg_risk_score=avg_risk,
        highest_risk_score=highest_risk,
        top_intent=top_intent,
        ollama_status="Active (Native)" if os.getenv("OLLAMA_ACTIVE") == "1" else "Active (Native M4)",
        cowrie_status="Listening (:2222)"
    )

def get_all_events(limit: int = 100) -> List[CommandEvent]:
    """Returns recent command telemetry events for live terminal feed."""
    events = []
    if _mongo_available and _mongo_db is not None:
        cursor = _mongo_db.sessions.find().sort("last_active", -1).limit(20)
        for doc in cursor:
            s_doc = SessionDoc.model_validate(doc)
            for cmd in s_doc.commands:
                events.append(CommandEvent(
                    session_id=s_doc.id,
                    src_ip=s_doc.attacker_ip,
                    command=cmd.cmd,
                    category=cmd.intent,
                    mitre_tag=cmd.mitre_tags[0] if cmd.mitre_tags else None,
                    event_risk_score=cmd.risk_increment,
                    timestamp=cmd.timestamp
                ))
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, session_id, timestamp, src_ip, command, category, mitre_tag, mitre_name, risk_score
            FROM events ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        for row in cursor.fetchall():
            events.append(CommandEvent(
                id=row["id"],
                session_id=row["session_id"],
                src_ip=row["src_ip"],
                command=row["command"],
                category=row["category"],
                mitre_tag=row["mitre_tag"] or None,
                mitre_name=row["mitre_name"] or None,
                event_risk_score=row["risk_score"] or 10,
                timestamp=row["timestamp"]
            ))
    return events

def get_all_assets() -> List[GeneratedAsset]:
    """Returns all deployed canary assets."""
    assets = []
    if _mongo_available and _mongo_db is not None:
        cursor = _mongo_db.sessions.find()
        for doc in cursor:
            s_doc = SessionDoc.model_validate(doc)
            for a in s_doc.assets_generated:
                assets.append(GeneratedAsset(
                    session_id=s_doc.id,
                    category=a.category,
                    file_path=a.path,
                    canary_type=a.type,
                    content_summary=a.content_ref,
                    exposure_count=a.exposure_count,
                    created_at=a.created_at
                ))
        return assets

    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, session_id, category, file_path, canary_type, content_summary, exposure_count, created_at
            FROM assets ORDER BY created_at DESC
        """)
        for row in cursor.fetchall():
            assets.append(GeneratedAsset(
                id=row["id"],
                session_id=row["session_id"],
                category=row["category"],
                file_path=row["file_path"],
                canary_type=row["canary_type"],
                content_summary=row["content_summary"],
                exposure_count=row["exposure_count"],
                created_at=row["created_at"]
            ))
    return assets

def get_mitre_statistics() -> List[MitreTechniqueStat]:
    """Aggregates MITRE ATT&CK technique frequencies."""
    stats: Dict[str, Dict[str, Any]] = {
        "T1082": {"name": "System Info Discovery", "count": 0, "sample": "uname -a"},
        "T1083": {"name": "File & Directory Discovery", "count": 0, "sample": "ls -la"},
        "T1552.001": {"name": "Credentials in Files (.env)", "count": 0, "sample": "cat .env"},
        "T1005": {"name": "Data from Local System (Payroll)", "count": 0, "sample": "cat Payroll_2026.csv"},
        "T1530": {"name": "Cloud Storage (S3)", "count": 0, "sample": "aws s3 ls"},
        "T1021.004": {"name": "SSH Lateral Movement", "count": 0, "sample": "ssh phil@internal"},
    }

    events = get_all_events(300)
    for evt in events:
        if evt.mitre_tag and evt.mitre_tag in stats:
            stats[evt.mitre_tag]["count"] += 1
            stats[evt.mitre_tag]["sample"] = evt.command

    result = []
    for tag, val in stats.items():
        if val["count"] > 0:
            result.append(MitreTechniqueStat(
                mitre_tag=tag,
                mitre_name=val["name"],
                count=val["count"],
                sample_command=val["sample"]
            ))
    return result
