"""
HoneyNet Asset Manager
Maintains the catalog of synthetic company assets, manages honeyfs filesystem seeding,
and tracks asset exposure per session.
"""
from typing import List, Dict, Any
from pathlib import Path
import shutil
import logging
from backend.config import TEMPLATES_DIR, HONEYFS_DIR

logger = logging.getLogger("honeynet.asset_manager")

# Static asset manifest for fast lookups
ASSET_MANIFEST = {
    "finance": [
        "Payroll_2026_Confidential.csv",
        "Budget_Q1_2026_Projections.txt",
        "Quarterly_Tax_Filings_2025.txt",
        "Wire_Transfer_Authorizations.txt"
    ],
    "git": [
        ".env",
        "repo/server.py",
        "repo/database.json",
        "repo/.git/config",
        "repo/.git/commit_history.log"
    ],
    "aws": [
        "credentials",
        "s3_buckets_dump.txt",
        "ec2_instances_internal.json"
    ],
    "hr": [
        "Employee_Directory_2026.csv",
        "Executive_Offer_Letter_CTO.txt",
        "Org_Chart_Confidential.txt",
        "Severance_Agreements_Q1.txt"
    ],
    "other": []
}

def get_assets_for_category(category: str) -> List[str]:
    """Returns the list of synthetic asset files associated with a category."""
    return ASSET_MANIFEST.get(category, [])

def scan_template_files(category: str) -> List[str]:
    """Scans the physical template folder to discover files on disk."""
    cat_dir = TEMPLATES_DIR / category
    if not cat_dir.exists() or not cat_dir.is_dir():
        return ASSET_MANIFEST.get(category, [])
        
    found_files = []
    for p in cat_dir.rglob("*"):
        if p.is_file():
            rel_p = str(p.relative_to(cat_dir))
            # Normalize env template name to .env in manifest
            if rel_p == "env.template" or rel_p == ".env.example":
                rel_p = ".env"
            found_files.append(rel_p)
            
    return found_files if found_files else ASSET_MANIFEST.get(category, [])

def seed_honeyfs_from_templates(force: bool = False) -> None:
    """
    Dynamically generates the Cowrie honeyfs virtual filesystem from safe templates.
    Generates honeyfs files at runtime without storing sensitive files in Git.
    """
    try:
        users = ["home/phil", "home/admin", "home/root", "root", "opt/corporate"]
        for user_prefix in users:
            for category in ["finance", "git", "aws", "hr"]:
                src_cat_dir = TEMPLATES_DIR / category
                dst_cat_dir = HONEYFS_DIR / user_prefix / category
                dst_cat_dir.mkdir(parents=True, exist_ok=True)
                
                if src_cat_dir.exists():
                    for item in src_cat_dir.iterdir():
                        if item.name in ("env.template", ".env.example", ".env"):
                            dst_file = dst_cat_dir / ".env"
                            if force or not dst_file.exists():
                                shutil.copy2(item, dst_file)
                        elif item.is_dir():
                            dst_subdir = dst_cat_dir / item.name
                            if force or not dst_subdir.exists():
                                shutil.copytree(item, dst_subdir, dirs_exist_ok=True)
                        else:
                            dst_file = dst_cat_dir / item.name
                            if force or not dst_file.exists():
                                shutil.copy2(item, dst_file)
        logger.info("HoneyFS virtual filesystem successfully seeded from templates.")
    except Exception as e:
        logger.warning(f"HoneyFS seeding notice: {e}")
