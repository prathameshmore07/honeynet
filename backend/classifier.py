"""
HoneyNet AI Intent Classifier
Interacts with local Ollama LLM with strict Pydantic validation
and zero-latency heuristic regex fallback.
"""
import re
import logging
import json
import httpx
import requests
from typing import Tuple, Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError

from backend.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, CATEGORIES

logger = logging.getLogger("honeynet.classifier")

class OllamaIntentResult(BaseModel):
    """Strict schema for Ollama AI structured output."""
    intent: str = Field(default="other")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    suggested_assets: List[str] = Field(default_factory=list)
    mitre_tags: List[str] = Field(default_factory=list)
    goal_hypothesis: str = Field(default="")

# Heuristic keyword matching patterns for fast/fallback classification
HEURISTIC_PATTERNS = {
    "finance": [
        r"(?<![a-zA-Z0-9])payroll(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])salary(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])salaries(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])tax(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])taxes(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])budget(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])wire(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])revenue(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])swift(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])bank(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])invoice(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])finance(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])accounting(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])compensation(?![a-zA-Z0-9])"
    ],
    "git": [
        r"(?<![a-zA-Z0-9])git(?![a-zA-Z0-9])",
        r"\.git(?![a-zA-Z0-9])",
        r"\.env(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])jwt(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])token(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])secret(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])repo(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])commit(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])github(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])gitlab(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])ssh-key(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])id_rsa(?![a-zA-Z0-9])",
        r"\.ssh(?![a-zA-Z0-9])"
    ],
    "aws": [
        r"(?<![a-zA-Z0-9])aws(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])s3(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])ec2(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])iam(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])bucket(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])credentials(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])boto3(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])sts(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])cloudformation(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])lambda(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])akia(?![a-zA-Z0-9])"
    ],
    "hr": [
        r"(?<![a-zA-Z0-9])employee(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])offer(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])org[-_]?chart(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])severance(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])personnel(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])headcount(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])ssn(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])hr(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])interview(?![a-zA-Z0-9])"
    ],
    "database": [
        r"(?<![a-zA-Z0-9])postgres(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])psql(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])mysql(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])sqlite(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])dump(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])schema(?![a-zA-Z0-9])",
        r"(?<![a-zA-Z0-9])select(?![a-zA-Z0-9])"
    ]
}

def normalize_response(raw_text: str) -> str:
    """Defensively parses and normalizes the AI model's response."""
    if not raw_text:
        return "other"
    clean_text = raw_text.lower().strip()
    clean_text = re.sub(r"[`*_#\(\)\[\]:\"']", " ", clean_text)
    for cat in ["finance", "git", "aws", "hr", "database", "other"]:
        if re.search(rf"\b{cat}\b", clean_text):
            return cat
    return "other"

def classify_with_heuristic(command: str) -> str:
    """Keyword-based intent classifier fallback."""
    cmd_lower = command.lower()
    for cat, patterns in HEURISTIC_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, cmd_lower):
                return cat
    return "other"

def check_ollama_health() -> Tuple[bool, str]:
    """Checks whether local Ollama daemon is reachable."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            has_model = any(OLLAMA_MODEL in m for m in models)
            if has_model:
                return True, f"Ollama operational ({OLLAMA_MODEL} active)"
            return True, f"Ollama reachable ({len(models)} models available)"
        return False, f"Ollama returned HTTP {resp.status_code}"
    except Exception as e:
        return False, f"Ollama offline ({type(e).__name__})"

def classify_with_ollama(command: str) -> Tuple[str, Optional[OllamaIntentResult]]:
    """Synchronous Ollama classification with strict Pydantic validation."""
    prompt = (
        f"You are a cybersecurity intent analyzer. An attacker executed: '{command}'.\n"
        f"Classify intent into exactly one of: finance, git, aws, hr, database, other.\n"
        f"Return ONLY valid JSON with keys: intent, confidence, suggested_assets, mitre_tags, goal_hypothesis."
    )
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0, "num_predict": 100}
    }

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )
        if resp.status_code == 200:
            raw_response = resp.json().get("response", "")
            try:
                parsed_json = json.loads(raw_response)
                result = OllamaIntentResult(**parsed_json)
                norm_cat = normalize_response(result.intent)
                return norm_cat, result
            except (json.JSONDecodeError, ValidationError):
                norm_cat = normalize_response(raw_response)
                return norm_cat, None
    except Exception as e:
        logger.debug(f"Ollama call skipped ({e})")
    
    return "other", None

def classify_command(command: str) -> Tuple[str, str]:
    """
    Two-Tier Intent Classifier:
    1. Heuristic fast-path
    2. Ollama LLM verification if ambiguous
    """
    heuristic_cat = classify_with_heuristic(command)
    if heuristic_cat != "other":
        return heuristic_cat, "heuristic_fast"
        
    ai_cat, _ = classify_with_ollama(command)
    if ai_cat != "other":
        return ai_cat, "ollama_ai"
        
    return "other", "default"

def warmup_classifier():
    """Initializes classifier and checks Ollama health."""
    ok, msg = check_ollama_health()
    logger.info(f"Ollama AI Health Check: {msg}")
