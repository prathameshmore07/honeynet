"""
HoneyNet Configuration Module
Uses pydantic-settings to validate environment configurations with strict typing.
Pure MongoDB storage configuration, zero hardcoded secrets.
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

    # Server & Security Settings
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    json_logs: bool = Field(default=True, alias="JSON_LOGS")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="ALLOWED_ORIGINS"
    )
    ws_auth_token: str = Field(
        default="honeynet_soc_token_2026",
        alias="WS_AUTH_TOKEN"
    )
    rate_limit_per_minute: int = Field(
        default=120,
        alias="RATE_LIMIT_PER_MINUTE"
    )

    # MongoDB Database
    mongo_uri: str = Field(default="mongodb://localhost:27017/honeynet_db", alias="MONGO_URI")
    database_url: str = Field(default="mongodb://localhost:27017/honeynet_db", alias="DATABASE_URL")
    database_name: str = Field(default="honeynet_db", alias="DATABASE_NAME")

    # Honeypot Logs & Paths
    cowrie_log_dir: Path = Field(default=BASE_DIR / "cowrie_logs")
    cowrie_log_path: Path = Field(default=BASE_DIR / "cowrie_logs" / "cowrie.json", alias="COWRIE_LOG_PATH")
    templates_dir: Path = Field(default=BASE_DIR / "templates")
    honeyfs_dir: Path = Field(default=BASE_DIR / "cowrie_config" / "honeyfs")

    # Ollama Local AI (M4 Apple Silicon Native)
    ollama_url: str = Field(default="http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="qwen2.5:3b", alias="OLLAMA_MODEL")
    ollama_timeout: float = Field(default=2.0, alias="OLLAMA_TIMEOUT")

    # Target Detection Categories
    categories: List[str] = ["finance", "git", "aws", "hr", "database", "other"]

# Global settings instance
settings = Settings()

# Backwards compatible exports
MONGO_URI = settings.mongo_uri
DATABASE_NAME = settings.database_name
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
