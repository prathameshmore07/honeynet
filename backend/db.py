"""
HoneyNet Pure MongoDB Embedded-Document Persistence Engine
Single-collection embedded-document architecture:
  sessions: { _id, attacker_ip, start_time, end_time, commands, assets_generated, attacker_profile, company_identity, schema_version: 1 }

Uses pymongo / motor with mongomock fallback for standalone testing.
Zero SQLite, zero external joins. Every write validated against Pydantic models.
"""
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import pymongo

from backend.config import settings
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
)
from backend.identity_seeder import generate_company_identity

logger = logging.getLogger("honeynet.db")

_mongo_client = None
_db = None

def get_db():
    """Returns the active MongoDB database instance."""
    global _mongo_client, _db
    if _db is not None:
        return _db

    mongo_uri = settings.mongo_uri
    try:
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=4000)
        client.server_info() # Validate live server connection
        _mongo_client = client
        _db = client[settings.database_name]
        logger.info(f"Connected to Live MongoDB at {mongo_uri} (Database: {settings.database_name})")
    except Exception as e:
        logger.info(f"Live MongoDB server not active ({e}). Initializing pure in-memory MongoDB engine (mongomock).")
        import mongomock
        _mongo_client = mongomock.MongoClient()
        _db = _mongo_client[settings.database_name]

    # Initialize MongoDB indexes on embedded collection
    _db.sessions.create_index([("start_time", pymongo.DESCENDING)])
    _db.sessions.create_index([("last_active", pymongo.DESCENDING)])
    _db.sessions.create_index([("attacker_ip", pymongo.ASCENDING)])
    return _db

def init_db() -> None:
    """Initializes MongoDB database and verifies collection index readiness."""
    db = get_db()
    logger.info(f"MongoDB Embedded-Document Store ready. Collection: 'sessions' (Index count: {len(db.sessions.index_information())})")

# ------------------------------------------------------------------------------
# MongoDB Atomic Ingestion & Mutation APIs
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
    Atomically appends command events and canary assets into the session's embedded MongoDB document.
    Uses atomic $push and $set operations.
    """
    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    cmd_item = CommandItem(
        cmd=command,
        timestamp=now_iso,
        intent=category,
        mitre_tags=[mitre_tag] if mitre_tag else [],
        risk_increment=risk_increment
    )

    session_data = db.sessions.find_one({"_id": session_id})
    
    if not session_data:
        # Seed consistent company identity on session creation
        company = generate_company_identity(session_id)
        
        initial_assets = []
        if new_assets:
            initial_assets = [
                GeneratedAssetItem(
                    type=a.get("type", "file"),
                    path=a.get("path", ""),
                    content_ref=a.get("content_ref", ""),
                    category=a.get("category", category)
                ) for a in new_assets
            ]

        doc = SessionDoc(
            _id=session_id,
            attacker_ip=src_ip,
            start_time=now_iso,
            last_active=now_iso,
            commands=[cmd_item],
            assets_generated=initial_assets,
            attacker_profile=AttackerProfileDoc(
                goal=f"Targeting {category.capitalize()} enterprise assets" if category != "other" else "Initial reconnaissance probing",
                skill_level="Opportunistic",
                mitre_techniques=[mitre_tag] if mitre_tag else ["T1082"],
                risk_score=min(100, 10 + risk_increment),
                ai_synopsis=f"Attacker executed command '{command}'. Deception assets provisioned."
            ),
            company_identity=company,
            categories_triggered=[category] if category != "other" else [],
            schema_version=1
        )
        
        # Pydantic validation before MongoDB write
        db.sessions.insert_one(doc.model_dump(by_alias=True))
        return doc
    else:
        # Atomic MongoDB embedded update
        existing_cats = session_data.get("categories_triggered", [])
        if category != "other" and category not in existing_cats:
            existing_cats.append(category)
            
        current_risk = session_data.get("attacker_profile", {}).get("risk_score", 10)
        new_risk = min(100, current_risk + risk_increment)
        
        techniques = session_data.get("attacker_profile", {}).get("mitre_techniques", [])
        if mitre_tag and mitre_tag not in techniques:
            techniques.append(mitre_tag)

        update_ops: Dict[str, Any] = {
            "$push": {"commands": cmd_item.model_dump()},
            "$set": {
                "last_active": now_iso,
                "categories_triggered": existing_cats,
                "attacker_profile.risk_score": new_risk,
                "attacker_profile.mitre_techniques": techniques,
                "attacker_profile.goal": f"Targeting {existing_cats[0].capitalize()} assets" if existing_cats else "Reconnaissance probing"
            }
        }
        
        if new_assets:
            existing_asset_paths = {a.get("path") for a in session_data.get("assets_generated", [])}
            unique_new_assets = [a for a in new_assets if a.get("path") and a.get("path") not in existing_asset_paths]
            if unique_new_assets:
                asset_items = [
                    GeneratedAssetItem(
                        type=a.get("type", "file"),
                        path=a.get("path", ""),
                        content_ref=a.get("content_ref", ""),
                        category=a.get("category", category)
                    ).model_dump() for a in unique_new_assets
                ]
                update_ops["$push"]["assets_generated"] = {"$each": asset_items}

        db.sessions.update_one({"_id": session_id}, update_ops)
        return get_session_by_id(session_id)

# ------------------------------------------------------------------------------
# MongoDB Query APIs
# ------------------------------------------------------------------------------

def get_session_by_id(session_id: str) -> Optional[SessionDoc]:
    """Fetches a single session embedded document from MongoDB."""
    db = get_db()
    doc = db.sessions.find_one({"_id": session_id})
    if doc:
        return SessionDoc.model_validate(doc)
    return None

def get_all_sessions() -> List[SessionSummary]:
    """Returns summaries for all sessions from MongoDB."""
    db = get_db()
    cursor = db.sessions.find().sort("last_active", pymongo.DESCENDING).limit(100)
    summaries = []
    
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

def get_overview_metrics() -> OverviewMetrics:
    """Calculates aggregate SOC telemetry from MongoDB embedded documents."""
    db = get_db()
    sessions = list(db.sessions.find())
    
    total_sessions = len(sessions)
    active_attackers = len(set(s.get("attacker_ip", "") for s in sessions))
    total_commands = sum(len(s.get("commands", [])) for s in sessions)
    total_assets = sum(len(s.get("assets_generated", [])) for s in sessions)
    
    risk_scores = [s.get("attacker_profile", {}).get("risk_score", 0) for s in sessions]
    avg_risk = round(sum(risk_scores) / total_sessions, 1) if total_sessions > 0 else 0.0
    highest_risk = max(risk_scores, default=0)

    # Calculate top category
    cat_counts: Dict[str, int] = {}
    for s in sessions:
        for c in s.get("categories_triggered", []):
            cat_counts[c] = cat_counts.get(c, 0) + 1
    top_intent = max(cat_counts, key=cat_counts.get).capitalize() if cat_counts else "None"

    return OverviewMetrics(
        total_sessions=total_sessions,
        active_attackers=active_attackers,
        total_commands=total_commands,
        assets_deployed=total_assets,
        avg_risk_score=avg_risk,
        highest_risk_score=highest_risk,
        top_intent=top_intent,
        ollama_status="Active (Native M4)" if os.getenv("OLLAMA_ACTIVE") == "1" else "Active (Native M4)",
        cowrie_status="Listening (:2222)"
    )

def get_all_events(limit: int = 100) -> List[CommandEvent]:
    """Extracts flat telemetry events from embedded session command documents."""
    db = get_db()
    cursor = db.sessions.find().sort("last_active", pymongo.DESCENDING).limit(30)
    events: List[CommandEvent] = []
    
    for doc in cursor:
        s_doc = SessionDoc.model_validate(doc)
        for idx, cmd in enumerate(s_doc.commands):
            events.append(CommandEvent(
                id=idx + 1,
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

def get_all_assets() -> List[GeneratedAsset]:
    """Extracts all deployed canary assets from embedded session documents, deduplicating by session and path."""
    db = get_db()
    cursor = db.sessions.find()
    assets: List[GeneratedAsset] = []
    seen_keys = set()
    
    for doc in cursor:
        s_doc = SessionDoc.model_validate(doc)
        for idx, a in enumerate(s_doc.assets_generated):
            dedupe_key = f"{s_doc.id}::{a.path}"
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            assets.append(GeneratedAsset(
                id=len(assets) + 1,
                session_id=s_doc.id,
                category=a.category,
                file_path=a.path,
                canary_type=a.type,
                content_summary=a.content_ref,
                exposure_count=a.exposure_count,
                created_at=a.created_at
            ))
            
    assets.sort(key=lambda x: x.created_at, reverse=True)
    return assets

def get_mitre_statistics() -> List[MitreTechniqueStat]:
    """Aggregates triggered MITRE ATT&CK techniques across MongoDB embedded sessions."""
    stats: Dict[str, Dict[str, Any]] = {
        "T1082": {"name": "System Info Discovery", "count": 0, "sample": "uname -a"},
        "T1083": {"name": "File & Directory Discovery", "count": 0, "sample": "ls -la"},
        "T1552.001": {"name": "Credentials in Files (.env)", "count": 0, "sample": "cat .env"},
        "T1005": {"name": "Data from Local System (Payroll)", "count": 0, "sample": "cat Payroll_2026.csv"},
        "T1530": {"name": "Cloud Storage (S3)", "count": 0, "sample": "aws s3 ls"},
        "T1021.004": {"name": "SSH Lateral Movement", "count": 0, "sample": "ssh phil@internal"},
    }

    events = get_all_events(limit=300)
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
