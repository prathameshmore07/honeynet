"""
HoneyNet Pydantic Data Models & MongoDB Embedded Document Schemas
Enforces strict type safety and validation on all database operations,
API inputs/outputs, and AI inferences.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

# ------------------------------------------------------------------------------
# 1. MongoDB Embedded Document Sub-models
# ------------------------------------------------------------------------------

class CommandItem(BaseModel):
    cmd: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    intent: str = "other"
    mitre_tags: List[str] = Field(default_factory=list)
    risk_increment: int = 10

class GeneratedAssetItem(BaseModel):
    type: str
    path: str
    content_ref: str
    category: str = "general"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    exposure_count: int = 1

class AttackerProfileDoc(BaseModel):
    goal: str = "Initial reconnaissance probing"
    skill_level: str = "Opportunistic"
    mitre_techniques: List[str] = Field(default_factory=list)
    risk_score: int = 10
    ai_synopsis: str = ""

class EmployeeIdentity(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: str
    salary: str
    annual_bonus: str

class CompanyIdentity(BaseModel):
    name: str
    domain: str
    tax_id: str
    industry: str
    headquarters: str
    employees: List[EmployeeIdentity] = Field(default_factory=list)

# ------------------------------------------------------------------------------
# 2. Main Session Document (Single Embedded Document in MongoDB)
# ------------------------------------------------------------------------------

class SessionDoc(BaseModel):
    id: str = Field(alias="_id")
    attacker_ip: str
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_active: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    commands: List[CommandItem] = Field(default_factory=list)
    assets_generated: List[GeneratedAssetItem] = Field(default_factory=list)
    attacker_profile: AttackerProfileDoc = Field(default_factory=AttackerProfileDoc)
    company_identity: Optional[CompanyIdentity] = None
    categories_triggered: List[str] = Field(default_factory=list)
    schema_version: int = 1

# ------------------------------------------------------------------------------
# 3. REST API / WebSocket Schemas
# ------------------------------------------------------------------------------

class CommandEvent(BaseModel):
    id: Optional[int] = None
    session_id: str
    src_ip: str
    command: str
    category: str = "other"
    classification_method: str = "heuristic_fast"
    files_served: List[str] = Field(default_factory=list)
    mitre_tag: Optional[str] = None
    mitre_name: Optional[str] = None
    event_risk_score: int = 10
    session_risk_score: Optional[int] = None
    skill_level: Optional[str] = None
    inferred_intent: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SessionSummary(BaseModel):
    session_id: str
    src_ip: str
    start_time: str
    last_active: str
    total_commands: int = 0
    categories_triggered: List[str] = Field(default_factory=list)
    risk_score: int = 0
    inferred_intent: str = "Reconnaissance"
    skill_level: str = "Opportunistic"
    goal_summary: str = "Initial reconnaissance probing"
    ai_summary: str = ""
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

class MitreTechniqueStat(BaseModel):
    mitre_tag: str
    mitre_name: str
    count: int
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
    ollama_status: str = "Active"
    cowrie_status: str = "Active"

class AttackPathNodeData(BaseModel):
    label: str
    nodeType: str
    ip: str
    service: str
    status: str
    icon: str

class AttackPathNode(BaseModel):
    id: str
    type: str = "custom"
    position: Dict[str, float]
    data: AttackPathNodeData

class AttackPathEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    animated: bool = False
    style: Optional[Dict[str, Any]] = None

class AttackPathGraph(BaseModel):
    nodes: List[AttackPathNode] = Field(default_factory=list)
    edges: List[AttackPathEdge] = Field(default_factory=list)

class SimulatorTriggerRequest(BaseModel):
    scenario: str = "finance"
    delay: float = 0.5
    ip: Optional[str] = None
