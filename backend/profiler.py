"""
HoneyNet Attacker Profiler & Threat Scoring Engine
Evaluates attacker sophistication, maps MITRE TTPs, computes composite risk scores (0-100),
and generates executive incident summaries.
"""
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger("honeynet.profiler")

def evaluate_attacker_profile(
    events: List[Dict[str, Any]],
    categories_triggered: List[str],
    current_risk: int
) -> Dict[str, Any]:
    """
    Computes attacker sophistication, goal hypothesis, composite risk score, and summary narrative.
    """
    cmd_count = len(events)
    cats = set(categories_triggered)
    
    # 1. Infer Skill Level
    # Advanced: multiple high-value categories, chained commands, AWS/DB exploitation
    if len(cats) >= 3 or ("aws" in cats and "git" in cats) or any("dump" in e.get("command", "") or "curl" in e.get("command", "") for e in events):
        skill_level = "APT / Sophisticated"
    elif len(cats) >= 1 or any(e.get("category", "") in ["finance", "git", "aws", "hr"] for e in events):
        skill_level = "Opportunistic Threat Actor"
    elif cmd_count > 10:
        skill_level = "Automated Scanner / Bot"
    else:
        skill_level = "Script Kiddie / Initial Probe"

    # 2. Inferred Goal & Intent
    if "finance" in cats and "hr" in cats:
        intent = "Corporate Espionage & PII Exfiltration"
        goal = "Targeting executive compensation, payroll spreadsheets, and confidential employee records for financial extortion."
    elif "aws" in cats and "git" in cats:
        intent = "Cloud Infrastructure & Credential Hijacking"
        goal = "Hunting for production .env API secrets, AWS access keys, and IAM roles to pivot into cloud VPC assets."
    elif "finance" in cats:
        intent = "Financial Data Exfiltration"
        goal = "Searching for wire transfer authorizations, quarterly financial projections, and corporate bank accounts."
    elif "git" in cats:
        intent = "Source Code & Secret Harvesting"
        goal = "Extracting proprietary codebase, database connection strings, and hardcoded API tokens."
    elif "aws" in cats:
        intent = "Cloud Asset Enumeration"
        goal = "Probing AWS S3 bucket dumps, EC2 instance mappings, and cloud backup vaults."
    elif "hr" in cats:
        intent = "Employee PII Harvesting"
        goal = "Compiling corporate directory, executive offer letters, and organizational hierarchy."
    else:
        intent = "System Discovery & Foothold Establishment"
        goal = "Probing host environment, operating system architecture, and local user privileges."

    # 3. Composite Risk Calculation (0-100)
    base_score = min(40, cmd_count * 4)
    cat_weight = len(cats) * 18
    high_value_penalty = 25 if ("aws" in cats or "git" in cats or "finance" in cats) else 0
    calculated_risk = min(100, max(current_risk, base_score + cat_weight + high_value_penalty))

    # 4. Executive Narrative Summary
    summary = (
        f"Attacker observed executing {cmd_count} interactive commands on honeypot bastion. "
        f"Behavior exhibits characteristics of a {skill_level} with primary focus on {intent.lower()}. "
        f"Active interest detected across {len(cats)} deception domain(s): {', '.join(cats) if cats else 'general OS'}. "
        f"Dynamic canary assets were deployed to entrap and monitor lateral movement."
    )

    return {
        "skill_level": skill_level,
        "inferred_intent": intent,
        "goal_summary": goal,
        "risk_score": calculated_risk,
        "ai_summary": summary
    }
