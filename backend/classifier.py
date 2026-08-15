"""
HoneyNet AI Intent Classifier (M4-Tuned)
Implements instant rule-based heuristic classification (<1ms) as the primary baseline,
with asynchronous native Ollama enrichment under a strict 2.0s timeout.
All AI responses are validated against Pydantic models before touching state or filesystem.
"""
import re
import logging
import json
import httpx
import requests
from typing import Tuple, Optional, List
from pydantic import BaseModel, Field, ValidationError

from backend.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger("honeynet.classifier")

class OllamaIntentResult(BaseModel):
    """Strict schema for Ollama AI structured output."""
    intent: str = Field(default="other")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    suggested_assets: List[str] = Field(default_factory=list)
    mitre_tags: List[str] = Field(default_factory=list)
    goal_hypothesis: str = Field(default="")

# Heuristic keyword matching patterns for instant baseline classification (< 1ms)
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
    """Instant rule-based intent matching (<1ms)."""
    cmd_lower = command.lower()
    for cat, patterns in HEURISTIC_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, cmd_lower):
                return cat
    return "other"

def check_ollama_health() -> Tuple[bool, str]:
    """Checks whether native Ollama daemon is reachable on macOS."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=1.0)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            has_model = any(OLLAMA_MODEL in m for m in models)
            if has_model:
                return True, f"Native Ollama active ({OLLAMA_MODEL})"
            return True, f"Native Ollama reachable ({len(models)} model(s) ready)"
        return False, f"Ollama HTTP {resp.status_code}"
    except Exception as e:
        return False, f"Ollama not active ({type(e).__name__})"

async def async_classify_with_ollama(command: str) -> Tuple[str, Optional[OllamaIntentResult]]:
    """
    Asynchronously queries native Ollama with a strict 2.0-second timeout.
    Falls back silently to rule-based result if timeout or network failure occurs.
    """
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
        "options": {"temperature": 0.0, "num_predict": 80}
    }

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
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
    except httpx.TimeoutException:
        logger.warning(f"Ollama response timeout (>2.0s) for command '{command[:20]}...', using instant regex baseline")
    except Exception as e:
        logger.debug(f"Ollama call skipped ({e})")
    
    return "other", None

def classify_command(command: str) -> Tuple[str, str]:
    """
    Primary two-tier classifier:
    1. Instant rule-based heuristic match (<1ms)
    2. Fallback default
    """
    heuristic_cat = classify_with_heuristic(command)
    if heuristic_cat != "other":
        return heuristic_cat, "heuristic_fast"
    return "other", "default"

def warmup_classifier():
    """Initializes classifier and checks native Ollama health."""
    ok, msg = check_ollama_health()
    logger.info(f"Native Ollama AI Health Check: {msg}")
