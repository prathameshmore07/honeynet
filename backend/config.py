"""
HoneyNet Configuration Module
Uses pydantic-settings to validate environment configurations with strict typing.
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """Central application settings with environment variable overrides."""
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server Settings
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    json_logs: bool = Field(default=True, alias="JSON_LOGS")

    # Database
    database_url: str = Field(default="", alias="DATABASE_URL")
    db_path: Path = Field(default=BASE_DIR / "honeynet.db", alias="HONEYNET_DB_PATH")

    # Honeypot Logs & Paths
    cowrie_log_dir: Path = Field(default=BASE_DIR / "cowrie_logs")
    cowrie_log_path: Path = Field(default=BASE_DIR / "cowrie_logs" / "cowrie.json", alias="COWRIE_LOG_PATH")
    templates_dir: Path = Field(default=BASE_DIR / "templates")
    honeyfs_dir: Path = Field(default=BASE_DIR / "cowrie_config" / "honeyfs")

    # Ollama Local AI
    ollama_url: str = Field(default="http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")
    ollama_timeout: float = Field(default=5.0, alias="OLLAMA_TIMEOUT")

    # Target Detection Categories
    categories: List[str] = ["finance", "git", "aws", "hr", "database", "other"]

# Global settings instance
settings = Settings()

# Backwards compatible exports
DB_PATH = settings.db_path
COWRIE_LOG_DIR = settings.cowrie_log_dir
COWRIE_LOG_PATH = settings.cowrie_log_path
TEMPLATES_DIR = settings.templates_dir
HONEYFS_DIR = settings.honeyfs_dir
OLLAMA_URL = settings.ollama_url
OLLAMA_MODEL = settings.ollama_model
OLLAMA_TIMEOUT = settings.ollama_timeout
CATEGORIES = settings.categories

# Ensure required directories exist
COWRIE_LOG_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
