"""
HoneyNet MITRE ATT&CK Mapper & Risk Scoring Engine
Maps observed attacker commands to MITRE ATT&CK techniques.
"""
import re
from typing import Tuple, Dict, Any

# MITRE ATT&CK Technique Definitions
TECHNIQUES = [
    {
        "id": "T1552.001",
        "name": "Credentials in Files",
        "tactic": "Credential Access",
        "risk": 45,
        "patterns": [
            r"\.env(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])credentials(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])id_rsa(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])jwt(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])secret(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])password(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])api[_-]?key(?![a-zA-Z0-9])"
        ]
    },
    {
        "id": "T1526",
        "name": "Cloud Service Discovery",
        "tactic": "Discovery",
        "risk": 40,
        "patterns": [
            r"(?<![a-zA-Z0-9])aws(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])s3(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])ec2(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])iam(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])bucket(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])sts(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])boto3(?![a-zA-Z0-9])"
        ]
    },
    {
        "id": "T1005",
        "name": "Data from Local System",
        "tactic": "Collection",
        "risk": 30,
        "patterns": [
            r"(?<![a-zA-Z0-9])cat(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])grep(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])tail(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])head(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])less(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])more(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])awk(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])strings(?![a-zA-Z0-9])"
        ]
    },
    {
        "id": "T1083",
        "name": "File and Directory Discovery",
        "tactic": "Discovery",
        "risk": 15,
        "patterns": [
            r"(?<![a-zA-Z0-9])ls(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])find(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])tree(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])pwd(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])dir(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])locat(e)?(?![a-zA-Z0-9])"
        ]
    },
    {
        "id": "T1082",
        "name": "System Information Discovery",
        "tactic": "Discovery",
        "risk": 10,
        "patterns": [
            r"(?<![a-zA-Z0-9])uname(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])hostname(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])uptime(?![a-zA-Z0-9])",
            r"/etc/os-release",
            r"/proc/cpuinfo"
        ]
    },
    {
        "id": "T1033",
        "name": "System Owner/User Discovery",
        "tactic": "Discovery",
        "risk": 10,
        "patterns": [
            r"(?<![a-zA-Z0-9])whoami(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])id(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])w(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])last(?![a-zA-Z0-9])",
            r"/etc/passwd"
        ]
    },
    {
        "id": "T1046",
        "name": "Network Service Discovery",
        "tactic": "Discovery",
        "risk": 20,
        "patterns": [
            r"(?<![a-zA-Z0-9])netstat(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])ss(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])nmap(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])arp(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])ifconfig(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])ip addr(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])ping(?![a-zA-Z0-9])"
        ]
    },
    {
        "id": "T1059.004",
        "name": "Unix Shell Execution",
        "tactic": "Execution",
        "risk": 10,
        "patterns": [
            r"(?<![a-zA-Z0-9])bash(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])sh(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])curl(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])wget(?![a-zA-Z0-9])",
            r"(?<![a-zA-Z0-9])python(?![a-zA-Z0-9])"
        ]
    }
]

def map_command_to_mitre(command: str, category: str = "other") -> Tuple[str, str, int]:
    """
    Evaluates a command against MITRE ATT&CK signature patterns and calculates risk score.
    Returns (mitre_id, mitre_name, risk_score).
    """
    cmd = command.lower()
    
    # Check signature patterns
    for tech in TECHNIQUES:
        for pat in tech["patterns"]:
            if re.search(pat, cmd):
                base_risk = tech["risk"]
                # Additional category multiplier if sensitive category triggered
                if category in ["finance", "git", "aws", "hr"]:
                    base_risk += 10
                return tech["id"], tech["name"], min(100, base_risk)
                
    # Fallback based on category
    if category == "finance":
        return "T1005", "Data from Local System (Financial Intelligence)", 35
    elif category == "git":
        return "T1552.001", "Credentials in Files (Source Repo / Env)", 40
    elif category == "aws":
        return "T1526", "Cloud Service Discovery (AWS Infrastructure)", 40
    elif category == "hr":
        return "T1005", "Data from Local System (Employee PII Records)", 30
        
    return "T1059.004", "Unix Shell Execution", 10
