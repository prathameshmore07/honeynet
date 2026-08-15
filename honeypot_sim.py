"""
HoneyNet Realistic Attack Simulator (V1 Scope)
Generates authentic Cowrie SSH attack telemetry targeting the V1 deception surfaces:
1. Finance & Payroll Spreadsheets (.xlsx, .csv, wire memos)
2. Developer Environment Secrets (.env)
3. AWS Cloud Backups (credentials, S3)
"""
import time
import json
import random
import argparse
from pathlib import Path
from datetime import datetime, timezone
import requests

from backend.config import COWRIE_LOG_PATH

SCENARIOS = {
    "finance": {
        "title": "Corporate Finance & Payroll Spreadsheet Exfiltration",
        "description": "Attacker targets executive compensation, payroll XLSX workbooks, and SWIFT wire logs.",
        "commands": [
            "whoami",
            "uname -a && id",
            "ls -la /home/phil",
            "ls -la /home/phil/finance/",
            "head -n 20 /home/phil/finance/Payroll_2026_Confidential.csv",
            "cat /home/phil/finance/Payroll_2026_Confidential.xlsx",
            "cat /home/phil/finance/Wire_Transfer_Authorizations.txt",
            "tar -czf /tmp/finance_dump.tar.gz /home/phil/finance/"
        ]
    },
    "git": {
        "title": "Developer Secrets & Production .env Discovery",
        "description": "Attacker searches filesystem for database credentials, JWT secrets, and Stripe tokens.",
        "commands": [
            "whoami",
            "find / -name '.env' 2>/dev/null",
            "ls -la /home/phil/git/",
            "cat /home/phil/git/.env",
            "git -C /home/phil/git log -n 5"
        ]
    },
    "aws": {
        "title": "AWS Cloud Infrastructure & S3 Reconnaissance",
        "description": "Attacker harvests AWS CLI credentials and queries corporate backup S3 buckets.",
        "commands": [
            "whoami",
            "cat ~/.aws/credentials 2>/dev/null || cat /home/phil/aws/credentials",
            "aws sts get-caller-identity",
            "aws s3 ls",
            "aws s3 sync s3://company-prod-backups-2026-vault /tmp/s3_loot"
        ]
    }
}

def generate_session_id() -> str:
    return f"session_{random.choice(['fin', 'ops', 'sec'])}_{random.randint(100, 999)}"

def generate_ip() -> str:
    octets = [str(random.randint(45, 198)), str(random.randint(10, 240)), str(random.randint(1, 250)), str(random.randint(1, 250))]
    return ".".join(octets)

def emit_file_event(session_id: str, src_ip: str, cmd: str):
    """Appends authentic Cowrie JSON line to cowrie_logs/cowrie.json."""
    event = {
        "eventid": "cowrie.command.input",
        "session": session_id,
        "src_ip": src_ip,
        "input": cmd,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    COWRIE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(COWRIE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
        f.flush()

def run_simulation(
    mode: str = "file",
    scenarios_to_run: list = None,
    delay: float = 0.4,
    override_ip: str = None
):
    if not scenarios_to_run:
        scenarios_to_run = ["finance"]

    session_id = generate_session_id()
    src_ip = override_ip or generate_ip()

    print("\n" + "=" * 56)
    print("  🛡️ HoneyNet Attack Simulator (V1 Scope)")
    print(f"  Session: {session_id} | IP: {src_ip} | Delay: {delay}s")
    print("=" * 56 + "\n")

    for sc_name in scenarios_to_run:
        sc_data = SCENARIOS.get(sc_name, SCENARIOS["finance"])
        print(f"\n>>> Executing Scenario: [{sc_data['title']}]")
        
        for cmd in sc_data["commands"]:
            print(f"  [EXEC >> Cowrie] $ {cmd}")
            emit_file_event(session_id, src_ip, cmd)
            time.sleep(delay)

    print("\n[✓] Simulation completed! View live telemetry on Next.js SOC dashboard.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HoneyNet V1 Attack Simulator")
    parser.add_argument("--scenario", choices=["finance", "git", "aws", "all"], default="finance")
    parser.add_argument("--delay", type=float, default=0.3)
    parser.add_argument("--ip", type=str, default=None)
    args = parser.parse_args()

    scenarios = ["finance", "git", "aws"] if args.scenario == "all" else [args.scenario]
    run_simulation(scenarios_to_run=scenarios, delay=args.delay, override_ip=args.ip)
