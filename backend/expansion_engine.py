"""
HoneyNet Lateral Movement & Environment Expansion Engine
Simulates enterprise topology expansion (Ubuntu Bastion -> GitLab -> Jenkins -> AWS -> DB -> HR -> Laptop)
and constructs React Flow graph data for real-time visualization.
"""
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger("honeynet.expansion")

TOPOLOGY_BLUEPRINT = [
    {
        "id": "node_bastion",
        "label": "Ubuntu SSH Bastion",
        "node_type": "host",
        "ip": "10.0.1.10 (Port 2222)",
        "service": "OpenSSH 8.9p1",
        "default_status": "compromised",
        "category_trigger": "initial",
        "position": {"x": 50, "y": 200},
        "icon": "server"
    },
    {
        "id": "node_gitlab",
        "label": "Internal GitLab Server",
        "node_type": "service",
        "ip": "10.0.2.15",
        "service": "GitLab Enterprise 16.4",
        "default_status": "discovered",
        "category_trigger": "git",
        "position": {"x": 280, "y": 80},
        "icon": "git-branch"
    },
    {
        "id": "node_jenkins",
        "label": "Jenkins CI/CD Worker",
        "node_type": "service",
        "ip": "10.0.2.20",
        "service": "Jenkins 2.440",
        "default_status": "dormant",
        "category_trigger": "git",
        "position": {"x": 520, "y": 80},
        "icon": "cpu"
    },
    {
        "id": "node_aws",
        "label": "AWS Cloud VPC (S3/EC2)",
        "node_type": "cloud",
        "ip": "10.0.3.5 / us-east-1",
        "service": "AWS IAM & S3 Vault",
        "default_status": "dormant",
        "category_trigger": "aws",
        "position": {"x": 280, "y": 320},
        "icon": "cloud"
    },
    {
        "id": "node_database",
        "label": "PostgreSQL Core DB Cluster",
        "node_type": "database",
        "ip": "10.0.4.12:5432",
        "service": "PostgreSQL 16.2 Master",
        "default_status": "dormant",
        "category_trigger": "database",
        "position": {"x": 520, "y": 320},
        "icon": "database"
    },
    {
        "id": "node_hr_portal",
        "label": "HR Internal Portal",
        "node_type": "service",
        "ip": "10.0.5.8:443",
        "service": "Workday / HRMS API",
        "default_status": "dormant",
        "category_trigger": "hr",
        "position": {"x": 750, "y": 140},
        "icon": "users"
    },
    {
        "id": "node_finance",
        "label": "Treasury & Finance Vault",
        "node_type": "service",
        "ip": "10.0.5.20",
        "service": "SWIFT / Banking Portal",
        "default_status": "dormant",
        "category_trigger": "finance",
        "position": {"x": 750, "y": 280},
        "icon": "dollar-sign"
    },
    {
        "id": "node_laptop",
        "label": "Executive CTO Workstation",
        "node_type": "host",
        "ip": "10.0.6.99",
        "service": "macOS 14 (Elena Vance)",
        "default_status": "dormant",
        "category_trigger": "finance",
        "position": {"x": 980, "y": 200},
        "icon": "laptop"
    }
]

TOPOLOGY_EDGES = [
    ("node_bastion", "node_gitlab", "Credential Hunt (.env)", "T1552.001"),
    ("node_gitlab", "node_jenkins", "Pipeline Token Exfil", "T1059.004"),
    ("node_bastion", "node_aws", "AWS Credentials Recon", "T1530"),
    ("node_aws", "node_database", "DB Snapshot Access", "T1005"),
    ("node_jenkins", "node_hr_portal", "Internal Service Pivot", "T1021.004"),
    ("node_database", "node_finance", "Payroll Query Exfil", "T1005"),
    ("node_hr_portal", "node_laptop", "Admin Token Impersonation", "T1078"),
    ("node_finance", "node_laptop", "Executive Target Lock", "T1560")
]

def build_attack_path_graph(categories_triggered: List[str], current_risk: int) -> Dict[str, Any]:
    """
    Constructs React Flow graph nodes and edges matching the current lateral attack state.
    """
    cats = set(categories_triggered)
    nodes = []
    
    # 1. Determine Node Statuses
    for blueprint in TOPOLOGY_BLUEPRINT:
        node_id = blueprint["id"]
        trigger = blueprint["category_trigger"]
        
        status = "dormant"
        if node_id == "node_bastion":
            status = "compromised"
        elif trigger in cats:
            status = "compromised" if current_risk > 50 else "targeted"
        elif any(c in cats for c in ["git", "aws", "finance", "hr"]):
            status = "discovered"
            
        nodes.append({
            "id": node_id,
            "type": "custom",
            "position": blueprint["position"],
            "data": {
                "label": blueprint["label"],
                "nodeType": blueprint["node_type"],
                "ip": blueprint["ip"],
                "service": blueprint["service"],
                "status": status,
                "icon": blueprint["icon"]
            }
        })

    # 2. Build Edges
    edges = []
    for idx, (src, dst, label, tech) in enumerate(TOPOLOGY_EDGES):
        src_node = next((n for n in nodes if n["id"] == src), None)
        dst_node = next((n for n in nodes if n["id"] == dst), None)
        
        is_active = (
            src_node and dst_node and 
            src_node["data"]["status"] in ["compromised", "targeted"] and
            dst_node["data"]["status"] in ["compromised", "targeted", "discovered"]
        )
        
        edges.append({
            "id": f"edge_{src}_{dst}",
            "source": src,
            "target": dst,
            "label": label,
            "animated": is_active,
            "style": {
                "stroke": "#06b6d4" if is_active else "#334155",
                "strokeWidth": 2 if is_active else 1,
                "strokeDasharray": "5,5" if not is_active else "none"
            },
            "data": {
                "technique": tech,
                "active": is_active
            }
        })

    return {
        "nodes": nodes,
        "edges": edges
    }
