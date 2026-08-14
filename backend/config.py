"""
HoneyNet Configuration Module
Uses dynamic relative paths to guarantee machine portability.
"""
from pathlib import Path
import os

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DB_PATH = Path(os.getenv("HONEYNET_DB_PATH", str(BASE_DIR / "honeynet.db")))

# Cowrie log path
COWRIE_LOG_DIR = BASE_DIR / "cowrie_logs"
COWRIE_LOG_PATH = Path(os.getenv("COWRIE_LOG_PATH", str(COWRIE_LOG_DIR / "cowrie.json")))

# Templates & HoneyFS directories
TEMPLATES_DIR = BASE_DIR / "templates"
HONEYFS_DIR = BASE_DIR / "cowrie_config" / "honeyfs"

# Ollama AI Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "5.0"))

# Target Category Set
CATEGORIES = ["finance", "git", "aws", "hr", "other"]

# Ensure essential local directories exist
COWRIE_LOG_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
