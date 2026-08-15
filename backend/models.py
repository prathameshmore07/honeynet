"""
HoneyNet Data Models & Schemas
Comprehensive Pydantic models for API responses, WebSockets, and database persistence.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class CommandEvent(BaseModel):
    id: Optional[int] = None
    session_id: str
    src_ip: str
    command: str
    category: str = "other"
    mitre_tag: Optional[str] = None
    mitre_name: Optional[str] = None
    event_risk_score: int = 10
    files_served: List[str] = Field(default_factory=list)
    timestamp: str

class SessionSummary(BaseModel):
    session_id: str
    src_ip: str
    start_time: str
    last_seen: str
    command_count: int = 0
    risk_score: int = 0
    inferred_intent: str = "Reconnaissance"
    skill_level: str = "Opportunistic"
    goal_summary: str = "Initial probing of honeypot environment"
    categories_targeted: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    pivot_depth: int = 1

class GeneratedAsset(BaseModel):
    id: Optional[int] = None
    session_id: str
    category: str
    file_path: str
    canary_type: str
    content_summary: str
    exposure_count: int = 1
    created_at: str

class AttackPathNode(BaseModel):
    id: str
    label: str
    node_type: str  # host, service, database, credential, cloud
    status: str     # compromised, discovered, targeted, bait_deployed
    ip_or_endpoint: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, float]] = None

class AttackPathEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    animated: bool = True
    technique: Optional[str] = None

class AttackPathGraph(BaseModel):
    session_id: str
    nodes: List[AttackPathNode] = Field(default_factory=list)
    edges: List[AttackPathEdge] = Field(default_factory=list)

class MitreTechniqueStat(BaseModel):
    tactic: str
    tech_id: str
    tech_name: str
    count: int = 0
    last_seen: Optional[str] = None
    sample_command: Optional[str] = None

class OverviewMetrics(BaseModel):
    total_sessions: int = 0
    active_attackers: int = 0
    total_commands: int = 0
    assets_deployed: int = 0
    avg_risk_score: float = 0.0
    highest_risk_score: int = 0
    top_intent: str = "None"
    ollama_status: str = "Ready"
    cowrie_status: str = "Active"

class SimulatorTriggerRequest(BaseModel):
    scenario: str = "full_apt"  # finance, git, aws, hr, full_apt
    delay: float = 0.5
    ip: Optional[str] = None

class WebSocketMessage(BaseModel):
    type: str  # command_event, asset_created, session_update, risk_alert
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
