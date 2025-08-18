from __future__ import annotations
from typing import Dict, Any
import json
import logging

from ..infra.settings import settings
from .prompts.intent_classification import (
    GROQ_INTENT_CLASSIFICATION_PROMPT, 
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


def _groq_client():
    try:
        from groq import Groq
    except Exception:
        return None
    if not settings.groq_api_key:
        return None
    try:
        return Groq(api_key=settings.groq_api_key)
    except Exception as e:
        logging.error(f"Failed to create Groq client: {e}")
        return None


def _classify_with_groq(text: str) -> list[str] | None:
    client = _groq_client()
    if not client:
        logging.error("Failed to create Groq client - check API key")
        return None
    
    prompt = GROQ_INTENT_CLASSIFICATION_PROMPT.format(
        intents=INTENTS,
        user_text=text
    )
    
    try:
        logging.info(f"Classifying intent for: {text[:50]}...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fastest option with good tool calling
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        
        out = response.choices[0].message.content.strip()
        logging.info(f"Groq response: {out}")
        
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
        logging.error(f"Groq API error: {e}")
        return None


def route_intent(text: str, context: Dict[str, Any] | None = None) -> list[str]:
    # Use Groq for intent classification with better error handling
    intents = _classify_with_groq(text)
    if not intents:
        # Fallback to heuristic if LLM fails
        logging.info("Groq classification failed, falling back to heuristic")
        intents = _heuristic_intent(text)
        if not intents or intents == ["agronomist"]:
            intents = ["general"]
    
    # If still classified as general, it means the query was unclear
    if intents == ["general"]:
        logging.info(f"Query classified as general, may need clarification: {text[:50]}...")
    
    return intents
