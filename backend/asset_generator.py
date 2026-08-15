"""
HoneyNet Dynamic Deception Asset Generator
Generates synthetic, internally-consistent fake files/folders matching inferred attacker intent
and injects them dynamically into Cowrie's honeyfs sandbox.
"""
import os
import shutil
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone

from backend.config import HONEYFS_DIR, TEMPLATES_DIR
from backend.db import record_asset

logger = logging.getLogger("honeynet.asset_generator")

# Asset Category Blueprints with canary types and descriptions
CATEGORY_BLUEPRINTS = {
    "finance": {
        "files": [
            ("Payroll_2026_Confidential.csv", "canary_pii_csv", "Confidential salary and compensation breakdown for 2026"),
            ("Budget_Q1_2026_Projections.txt", "canary_financial_doc", "Q1 operating budget and capital expenditure projections"),
            ("Quarterly_Tax_Filings_2025.txt", "canary_financial_doc", "Corporate IRS tax filing reconciliation summary"),
            ("Wire_Transfer_Authorizations.txt", "canary_banking_token", "Authorized dual-key SWIFT wire transfer templates")
        ]
    },
    "git": {
        "files": [
            (".env", "canary_api_keys", "Production application environment variables and mock tokens"),
            ("repo/server.py", "canary_source_code", "Internal microservice authentication API server"),
            ("repo/database.json", "canary_db_config", "Cluster replication and database connection parameters"),
            ("repo/.git/config", "canary_git_config", "GitLab internal repository origin configuration"),
            ("repo/.git/commit_history.log", "canary_git_log", "Git commit history referencing sanitized secrets")
        ]
    },
    "aws": {
        "files": [
            ("credentials", "canary_aws_keys", "AWS CLI multi-profile access key configuration"),
            ("s3_buckets_dump.txt", "canary_s3_manifest", "Listing of internal S3 enterprise backup buckets"),
            ("ec2_instances_internal.json", "canary_cloud_inventory", "EC2 cloud topology with security zone mappings")
        ]
    },
    "hr": {
        "files": [
            ("Employee_Directory_2026.csv", "canary_pii_directory", "Complete staff roster with internal extensions and clearances"),
            ("Executive_Offer_Letter_CTO.txt", "canary_executive_doc", "C-suite employment agreement and equity schedule"),
            ("Org_Chart_Confidential.txt", "canary_org_structure", "Internal hierarchical reporting chain and security officers"),
            ("Severance_Agreements_Q1.txt", "canary_legal_doc", "Q1 restructuring severance covenants and settlement amounts")
        ]
    },
    "database": {
        "files": [
            ("pg_dump_core_2026.sql", "canary_db_dump", "PostgreSQL schema dump with fake user hashes"),
            ("db_connection_pool.conf", "canary_db_config", "High-availability connection pooling config for 10.0.4.12")
        ]
    }
}

DYNAMIC_TEMPLATES = {
    "database/pg_dump_core_2026.sql": """-- PostgreSQL Database Dump: core_production
-- Host: 10.0.4.12    Database: core_production
-- Backup Time: 2026-02-14 03:00:01 UTC

CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(128) NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(32) DEFAULT 'standard',
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO public.users (username, email, password_hash, role) VALUES
('elena.vance', 'elena.vance@apexdynamics.io', '$2b$12$eX4mPL3sYnThEt1cHaShF0rD3cEpT10n0nLy00000000001', 'executive_admin'),
('devon.chen', 'devon.chen@apexdynamics.io', '$2b$12$eX4mPL3sYnThEt1cHaShF0rD3cEpT10n0nLy00000000002', 'infra_lead'),
('sarah.m', 'sarah.m@apexdynamics.io', '$2b$12$eX4mPL3sYnThEt1cHaShF0rD3cEpT10n0nLy00000000003', 'secops_analyst');
""",
    "database/db_connection_pool.conf": """# Core Database Connection Pool Configuration
[postgres_cluster]
master_host = 10.0.4.12
port = 5432
dbname = core_production
user = app_prod_master
pool_size = 25
max_overflow = 50
sslmode = require
read_replicas = 10.0.4.13,10.0.4.14
"""
}

def generate_assets_for_intent(session_id: str, category: str, username: str = "phil") -> List[Dict[str, Any]]:
    """
    Dynamically generates and provisions deceptive assets into Cowrie's honeyfs sandbox
    matching the attacker's inferred intent.
    """
    if category not in CATEGORY_BLUEPRINTS:
        return []

    deployed_assets = []
    blueprint = CATEGORY_BLUEPRINTS[category]
    user_paths = [f"home/{username}", "home/admin", "opt/corporate", "root"]

    for filename, canary_type, description in blueprint["files"]:
        src_template = TEMPLATES_DIR / category / (filename if filename != ".env" else "env.template")
        
        # If template exists in templates/
        content = None
        if src_template.exists() and src_template.is_file():
            try:
                content = src_template.read_text()
            except Exception:
                pass
        
        # Check dynamic templates dictionary
        dynamic_key = f"{category}/{filename}"
        if not content and dynamic_key in DYNAMIC_TEMPLATES:
            content = DYNAMIC_TEMPLATES[dynamic_key]
            
        if not content:
            content = f"# Deception Asset: {filename}\n# Synthetic asset generated for session {session_id}\n"

        # Deploy into honeyfs for target paths
        primary_rel_path = f"/home/{username}/{category}/{filename}"
        for upath in user_paths:
            dst_file = HONEYFS_DIR / upath / category / filename
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                dst_file.write_text(content)
            except Exception as e:
                logger.warning(f"Failed writing dynamic asset to {dst_file}: {e}")

        # Record asset in database
        asset_id = record_asset(
            session_id=session_id,
            category=category,
            file_path=primary_rel_path,
            canary_type=canary_type,
            content_summary=description
        )

        deployed_assets.append({
            "id": asset_id,
            "category": category,
            "file_path": primary_rel_path,
            "canary_type": canary_type,
            "description": description
        })

    logger.info(f"[+] Dynamically deployed {len(deployed_assets)} {category} deception assets for session {session_id}")
    return deployed_assets
