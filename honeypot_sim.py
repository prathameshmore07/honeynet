#!/usr/bin/env python3
"""
HoneyNet Multi-Session Attack Simulator
Simulates realistic attacker sessions by generating authentic Cowrie JSON log streams
for demo and testing purposes.
"""
import time
import json
import random
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from backend.config import COWRIE_LOG_PATH, BASE_DIR

SCENARIOS = {
    "finance": {
        "name": "Financial Data Scout",
        "ip": "45.33.32.156",
        "commands": [
            "whoami",
            "uname -a",
            "find / -name '*payroll*' 2>/dev/null",
            "ls -la /home/phil/finance/",
            "cat /home/phil/finance/Payroll_2026_Confidential.csv",
            "grep -i 'Executive' /home/phil/finance/Payroll_2026_Confidential.csv",
            "cat /home/phil/finance/Wire_Transfer_Authorizations.txt"
        ]
    },
    "git": {
        "name": "Git & Credential Hunter",
        "ip": "185.220.101.5",
        "commands": [
            "id",
            "ls -la",
            "find / -name '.env' 2>/dev/null",
            "cat /home/phil/git/.env",
            "git log -n 5 --oneline",
            "cat /home/phil/git/repo/database.json"
        ]
    },
    "aws": {
        "name": "AWS Cloud Infrastructure Recon",
        "ip": "103.251.167.20",
        "commands": [
            "env",
            "cat ~/.aws/credentials 2>/dev/null || cat /home/phil/aws/credentials",
            "aws s3 ls",
            "cat /home/phil/aws/s3_buckets_dump.txt",
            "aws ec2 describe-instances --region us-east-1"
        ]
    },
    "hr": {
        "name": "HR & Employee PII Exfiltration",
        "ip": "194.26.29.112",
        "commands": [
            "w",
            "find / -name '*employee*' 2>/dev/null",
            "cat /home/phil/hr/Employee_Directory_2026.csv",
            "cat /home/phil/hr/Executive_Offer_Letter_CTO.txt",
            "cat /home/phil/hr/Org_Chart_Confidential.txt"
        ]
    },
    "full_apt": {
        "name": "Full Multi-Stage APT Lateral Pivot Chain",
        "ip": "91.240.118.82",
        "commands": [
            "whoami",
            "uname -a && id",
            "find / -name '.env' 2>/dev/null",
            "cat /home/phil/git/.env",
            "cat ~/.aws/credentials 2>/dev/null || cat /home/phil/aws/credentials",
            "aws s3 ls s3://apex-prod-backups-2026-vault",
            "cat /home/phil/finance/Payroll_2026_Confidential.csv",
            "cat /home/phil/hr/Org_Chart_Confidential.txt",
            "cat /home/phil/finance/Wire_Transfer_Authorizations.txt"
        ]
    }
}

def generate_cowrie_log_entry(session_id: str, src_ip: str, command: str) -> str:
    """Formats an authentic Cowrie JSON log entry."""
    entry = {
        "eventid": "cowrie.command.input",
        "session": session_id,
        "src_ip": src_ip,
        "src_port": random.randint(40000, 65000),
        "dst_ip": "10.0.1.10",
        "dst_port": 2222,
        "input": command,
        "message": f"CMD: {command}",
        "sensor": "srv-prod-core-01",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return json.dumps(entry)

def run_simulation(
    mode: str = "file",
    scenarios_to_run: Optional[List[str]] = None,
    delay: float = 0.5,
    override_ip: Optional[str] = None
):
    """Executes the attack simulation across selected scenarios."""
    scenarios_to_run = scenarios_to_run or list(SCENARIOS.keys())
    print(f"\n========================================================")
    print(f"  🛡️ HoneyNet Attack Simulator Starting")
    print(f"  Mode: {mode.upper()} | Delay: {delay}s | Scenarios: {', '.join(scenarios_to_run)}")
    print(f"========================================================\n")

    COWRIE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    for sc_key in scenarios_to_run:
        if sc_key not in SCENARIOS:
            print(f"[!] Unknown scenario: {sc_key}")
            continue

        sc = SCENARIOS[sc_key]
        session_id = f"{sc_key}_{hex(random.randint(1000, 9999))[2:]}"
        src_ip = override_ip or sc["ip"]

        print(f"\n>>> Starting Scenario: [{sc['name']}] (Session: {session_id} | IP: {src_ip})")

        with open(COWRIE_LOG_PATH, "a", encoding="utf-8") as f:
            for cmd in sc["commands"]:
                entry = generate_cowrie_log_entry(session_id, src_ip, cmd)
                f.write(entry + "\n")
                f.flush()
                print(f"  [LOG >> cowrie.json] {cmd}")
                time.sleep(delay)

    print(f"\n[+] Simulation complete! View results on the Next.js SOC dashboard.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HoneyNet Multi-Session Attack Simulator")
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()) + ["all"], default="all", help="Scenario to run")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between commands in seconds")
    parser.add_argument("--ip", type=str, default=None, help="Optional IP override")
    args = parser.parse_args()

    scenarios = list(SCENARIOS.keys()) if args.scenario == "all" else [args.scenario]
    run_simulation(scenarios_to_run=scenarios, delay=args.delay, override_ip=args.ip)
