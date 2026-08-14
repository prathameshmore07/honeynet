#!/usr/bin/env python3
"""
HoneyNet Multi-Session Attack Simulator
Simulates realistic attacker sessions by generating authentic Cowrie JSON log streams
or sending commands directly to the FastAPI simulation endpoint.
"""
import time
import json
import random
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

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
    }
}

def generate_cowrie_log_entry(session_id: str, src_ip: str, command: str) -> str:
    """Formats an authentic Cowrie JSON log entry."""
    entry = {
        "eventid": "cowrie.command.input",
        "session": session_id,
        "src_ip": src_ip,
        "src_port": random.randint(40000, 65000),
        "dst_ip": "10.0.0.1",
        "dst_port": 2222,
        "input": command,
        "message": f"CMD: {command}",
        "sensor": "srv-prod-core-01",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return json.dumps(entry)

def run_simulation(
    mode: str = "file",
    scenarios_to_run: list = None,
    delay: float = 0.8,
    api_url: str = "http://localhost:8000"
):
    """Executes the simulation across selected scenarios."""
    scenarios_to_run = scenarios_to_run or list(SCENARIOS.keys())
    print(f"\n========================================================")
    print(f"  HoneyNet Attack Simulator Starting")
    print(f"  Mode: {mode.upper()} | Delay: {delay}s | Scenarios: {', '.join(scenarios_to_run)}")
    print(f"========================================================\n")

    COWRIE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    for sc_key in scenarios_to_run:
        if sc_key not in SCENARIOS:
            print(f"[!] Unknown scenario: {sc_key}")
            continue

        sc = SCENARIOS[sc_key]
        session_id = f"{sc_key}_{random.randint(1000, 9999):x}"
        print(f"\n>>> Starting Scenario: [{sc['name']}] (Session: {session_id} | IP: {sc['ip']})")

        for cmd in sc["commands"]:
            if mode == "file":
                log_line = generate_cowrie_log_entry(session_id, sc["ip"], cmd)
                with open(COWRIE_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
                    f.flush()
                print(f"  [LOG >> cowrie.json] {cmd}")
            else:
                try:
                    payload = {
                        "session_id": session_id,
                        "src_ip": sc["ip"],
                        "command": cmd,
                        "scenario": sc_key
                    }
                    resp = requests.post(f"{api_url}/api/simulate", json=payload, timeout=5.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        cat = data.get("category", "other")
                        mitre = data.get("mitre_tag", "")
                        print(f"  [API >>] {cmd:45} | Cat: {cat:8} | MITRE: {mitre}")
                    else:
                        print(f"  [API ERROR {resp.status_code}] {cmd}")
                except Exception as e:
                    print(f"  [API Connection Failed: {e}] {cmd}")

            time.sleep(delay)

    print(f"\n[+] Simulation complete! View results on the Streamlit dashboard.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HoneyNet Multi-Session Attack Simulator")
    parser.add_argument("--mode", choices=["file", "api"], default="file", help="Simulation mode: write to cowrie.json file or call FastAPI endpoint")
    parser.add_argument("--scenario", choices=["finance", "git", "aws", "hr", "all"], default="all", help="Attack scenario to run")
    parser.add_argument("--delay", type=float, default=0.8, help="Delay in seconds between commands")
    parser.add_argument("--api-url", default="http://localhost:8000", help="FastAPI backend URL (for api mode)")

    args = parser.parse_args()
    selected = list(SCENARIOS.keys()) if args.scenario == "all" else [args.scenario]
    run_simulation(mode=args.mode, scenarios_to_run=selected, delay=args.delay, api_url=args.api_url)
