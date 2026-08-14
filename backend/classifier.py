"""
HoneyNet AI Intent Classifier
Interacts with local Ollama with fallback heuristic classification.
"""
import re
import logging
import requests
from typing import Tuple
from backend.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, CATEGORIES

logger = logging.getLogger("honeynet.classifier")

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
    ]
}

def normalize_response(raw_text: str) -> str:
    """
    Defensively parses and normalizes the AI model's response.
    Handles markdown wrappers, prefixes (e.g. 'Category: finance'), and punctuation.
    """
    if not raw_text:
        return "other"
    
    clean_text = raw_text.lower().strip()
    clean_text = re.sub(r"[`*_#\(\)\[\]:\"']", " ", clean_text)
    
    # Priority order matching for exact tokens
    for cat in ["finance", "git", "aws", "hr", "other"]:
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
    """
    Checks if Ollama is running and whether the target model is available.
    Returns (is_healthy, status_message).
    """
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2.0)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Check if requested model (or base name) is present
            target_base = OLLAMA_MODEL.split(":")[0]
            matched = any(target_base in name for name in model_names)
            
            if matched:
                return True, f"Ollama is running with model '{OLLAMA_MODEL}'."
            else:
                available_str = ", ".join(model_names) if model_names else "none"
                return True, f"Ollama is up, but model '{OLLAMA_MODEL}' is not pulled yet (Available: {available_str}). Run: 'ollama pull {OLLAMA_MODEL}'."
        return False, f"Ollama returned HTTP status {resp.status_code}."
    except requests.exceptions.RequestException as e:
        return False, f"Cannot connect to Ollama at {OLLAMA_URL} ({type(e).__name__}). Using heuristic classifier fallback."

def warmup_classifier() -> None:
    """Pre-warms the Ollama model at startup to avoid first-call latency."""
    health_ok, msg = check_ollama_health()
    logger.info(f"Ollama health check: {msg}")
    
    if not health_ok:
        logger.warning("Skipping Ollama warmup; heuristic fallback is active.")
        return
        
    try:
        dummy_prompt = (
            "Classify this attacker command into exactly one word: "
            "finance, git, aws, hr, or other. Command: ls -la"
        )
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": dummy_prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 10}
        }
        requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=OLLAMA_TIMEOUT)
        logger.info("Ollama model successfully pre-warmed.")
    except Exception as e:
        logger.warning(f"Ollama warmup failed: {e}. Fallback heuristics will be used if needed.")

def classify_command(command: str) -> Tuple[str, str]:
    """
    Classifies an attacker command into one of: finance, git, aws, hr, or other.
    Returns tuple of (category, method_used: 'ai' | 'heuristic').
    """
    cmd = (command or "").strip()
    if not cmd:
        return "other", "heuristic"
        
    prompt = (
        f"Classify this attacker command into exactly one word: "
        f"finance, git, aws, hr, or other. Command: {cmd}"
    )
    
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 10
            }
        }
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=OLLAMA_TIMEOUT)
        if resp.status_code == 200:
            raw_response = resp.json().get("response", "")
            category = normalize_response(raw_response)
            return category, "ai"
    except Exception as e:
        logger.debug(f"Ollama call failed or timed out ({e}). Falling back to heuristic classifier.")
        
    # Heuristic fallback
    category = classify_with_heuristic(cmd)
    return category, "heuristic"

def generate_attacker_summary(commands: list) -> str:
    """
    Generates a concise 1-2 sentence AI summary of attacker's intent.
    Falls back to structured rule-based summary if Ollama is unavailable.
    """
    if not commands:
        return "No commands executed in this session yet."
        
    cmd_sample = " | ".join(commands[-8:])
    prompt = (
        f"In one concise sentence (maximum 20 words), summarize what this cyber attacker is attempting to do: {cmd_sample}"
    )
    
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 40
            }
        }
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=OLLAMA_TIMEOUT)
        if resp.status_code == 200:
            summary = resp.json().get("response", "").strip()
            # Clean up summary
            summary = summary.replace("\n", " ").strip('"\': ')
            if len(summary) > 10:
                return summary
    except Exception:
        pass
        
    # Heuristic summary
    cats_found = set()
    for c in commands:
        cat = classify_with_heuristic(c)
        if cat != "other":
            cats_found.add(cat)
            
    if not cats_found:
        return "Initial reconnaissance: Attacker is surveying the system environment and exploring directories."
    cat_str = ", ".join(sorted(cats_found))
    return f"Targeted credential & asset hunting: Attacker focused on accessing {cat_str} assets."
