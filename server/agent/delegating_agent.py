from __future__ import annotations
from typing import Dict, Any
import json
import logging

from ..infra.settings import settings
from .prompts.intent_classification import (
    GEMINI_INTENT_CLASSIFICATION_PROMPT, 
    INTENT_KEYWORDS,
    SUPPORTED_INTENTS
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
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception:
        return None


def _classify_with_gemini(text: str) -> list[str] | None:
    model = _gemini_model()
    if not model:
        logging.error("Failed to create Gemini model - check API key")
        return None
    
    prompt = GEMINI_INTENT_CLASSIFICATION_PROMPT.format(
        intents=INTENTS,
        user_text=text
    )
    
    try:
        logging.info(f"Classifying intent for: {text[:50]}...")
        resp = model.generate_content(prompt)
        out = (getattr(resp, "text", None) or "").strip()
        logging.info(f"Gemini response: {out}")
        
        # Clean JSON from markdown code blocks
        clean_json = out
        if out.startswith("```json") and out.endswith("```"):
            clean_json = out[7:-3].strip()
        elif out.startswith("```") and out.endswith("```"):
            clean_json = out[3:-3].strip()
        
        data = json.loads(clean_json)
        intents = data.get("intents", [])
        if not isinstance(intents, list):
            logging.warning(f"Invalid intents format: {intents}")
            return None
        
        valid_intents = [i for i in intents if i in INTENTS]
        logging.info(f"Valid intents found: {valid_intents}")
        return valid_intents if valid_intents else None
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing failed: {e}, cleaned response: {clean_json}")
        return None
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        return None


def route_intent(text: str, context: Dict[str, Any] | None = None) -> list[str]:
    # Only use Gemini for intent classification - no keyword fallback
    intents = _classify_with_gemini(text)
    if not intents:
        # Default to general if LLM fails
        intents = ["general"]
    return intents
