from __future__ import annotations
from typing import Dict, Any
import json

from ...infra.settings import settings

INTENTS = ["market", "weather", "govt_policy", "agronomist", "IoT_info"]


def _heuristic_intent(text: str) -> list[str]:
    t = (text or "").lower()
    detected = []
    
    if any(w in t for w in ["weather", "rain", "temperature", "forecast", "wind", "humid", "humidity", "sun", "monsoon"]):
        detected.append("weather")
    if any(w in t for w in ["price", "market", "mandi", "sell", "rate", "wholesale", "buyer", "auction"]):
        detected.append("market")
    if any(w in t for w in ["policy", "government", "scheme", "subsidy", "loan", "credit", "regulation", "law"]):
        detected.append("govt_policy")
    if any(w in t for w in ["crop", "suitable", "variety", "sowing", "planting", "yield", "irrigation", "fertilizer", "pest", "disease", "seed", "soil", "nutrition", "expert", "advice"]):
        detected.append("agronomist")
    if any(w in t for w in ["sensor", "iot", "device", "monitor", "data", "smart", "automation", "technology", "equipment"]):
        detected.append("IoT_info")
    
    return detected if detected else ["agronomist"]  # default fallback


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
    prompt = (
        "You are an intent classifier for a farming assistant.\n"
        f"Allowed intents: {INTENTS}.\n"
        "Given the user text, output ONLY a compact JSON object with exactly one key 'intents' whose value is an array of relevant intents.\n"
        "Multiple intents are allowed if the query spans multiple domains.\n"
        "No extra text.\n"
        "Examples:\n"
        "USER: Will it rain tomorrow?\nOUTPUT: {\"intents\": [\"weather\"]}\n"
        "USER: Tomato prices near Nashik\nOUTPUT: {\"intents\": [\"market\"]}\n"
        "USER: What seed variety suits this unpredictable weather?\nOUTPUT: {\"intents\": [\"weather\", \"agronomist\"]}\n"
        "USER: Government subsidies for drip irrigation?\nOUTPUT: {\"intents\": [\"govt_policy\", \"IoT_info\"]}\n"
        f"USER: {text}\nOUTPUT:"
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
