from __future__ import annotations
from typing import Dict, Any
import json

from ..infra.settings import settings
from .prompts.intent_classification import (
    SUPPORTED_INTENTS, 
    INTENT_KEYWORDS, 
    GEMINI_INTENT_CLASSIFICATION_PROMPT
)

INTENTS = SUPPORTED_INTENTS


def _heuristic_intent(text: str) -> list[str]:
    t = (text or "").lower()
    detected = []
    
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(w in t for w in keywords):
            detected.append(intent)
    
    return detected if detected else ["agronomist"]


def _gemini_model():
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        return None
    if not settings.gemini_api_key:
        return None
    try:
        genai.configure(api_key=settings.gemini_api_key)
        return genai.GenerativeModel("gemini-1.5-pro")
    except Exception:
        return None


def _classify_with_gemini(text: str) -> list[str] | None:
    model = _gemini_model()
    if not model:
        return None
    prompt = GEMINI_INTENT_CLASSIFICATION_PROMPT.format(
        intents=INTENTS,
        user_text=text
    )
    try:
        resp = model.generate_content(prompt)
        out = (getattr(resp, "text", None) or "").strip()
        data = json.loads(out)
        intents = data.get("intents", [])
        if not isinstance(intents, list):
            return None
        valid_intents = [i for i in intents if i in INTENTS]
        return valid_intents if valid_intents else None
    except Exception:
        return None


def route_intent(text: str, context: Dict[str, Any] | None = None) -> list[str]:
    # Try Gemini first (if configured), else fallback to heuristic
    intents = _classify_with_gemini(text)
    if not intents:
        intents = _heuristic_intent(text)
    return intents
