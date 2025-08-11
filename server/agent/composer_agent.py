from __future__ import annotations
from typing import Any, Dict, List
import json
import os

from ...infra.settings import settings

# Gemini LLM (optional)
try:
    import google.generativeai as genai  # type: ignore
    _GEMINI_AVAILABLE = True
except Exception:  # pragma: no cover
    _GEMINI_AVAILABLE = False


SYS_PROMPT = (
    "You are Sherkari's Answer Composer. You MUST produce a helpful,"
    " concise advisory ONLY using the provided tool outputs. Do not invent facts."
    " Always include a TL;DR and numbered steps. End with citations array."
)


def _gemini_client():
    if not settings.gemini_api_key or not _GEMINI_AVAILABLE:
        return None
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel("gemini-1.5-pro")


def compose_answer(tools_used: List[Dict[str, Any]], intent: str, locale: str | None = None) -> Dict[str, Any]:
    """Compose final answer. Falls back to deterministic template if no LLM key.

    Returns dict with {text, citations}
    """
    citations: List[Dict[str, Any]] = []
    for t in tools_used:
        data = t.get("output", {})
        srcs = data.get("sources") or data.get("source_urls") or []
        if isinstance(srcs, dict):
            srcs = [srcs]
        for s in srcs:
            if isinstance(s, str):
                citations.append({"url": s, "tool": t["name"]})
            elif isinstance(s, dict):
                s = {k: v for k, v in s.items() if k in {"url", "title", "page"}}
                s["tool"] = t["name"]
                citations.append(s)

    # If Gemini is available, use it to craft natural text constrained to tools
    client = _gemini_client()
    if client:
        tool_summaries = json.dumps({t["name"]: t.get("output", {}) for t in tools_used})
        prompt = (
            f"{SYS_PROMPT}\n\n"
            f"Intent: {intent}. Locale: {locale or 'en-IN'}.\n"
            f"TOOL_RESULTS_JSON: {tool_summaries}\n"
            f"Compose a user-facing answer strictly from TOOL_RESULTS_JSON."
        )
        try:
            resp = client.generate_content(prompt)
            text = resp.text or ""
        except Exception as e:  # fallback
            text = _fallback_text(tools_used, intent)
    else:
        text = _fallback_text(tools_used, intent)

    return {"text": text, "citations": citations}


def _fallback_text(tools_used: List[Dict[str, Any]], intent: str) -> str:
    # User-friendly deterministic text without exposing internal details
    if intent == "general":
        return (
            "I can help with farm weather and market prices.\n"
            "- Ask things like: 'Weather for the next 3 days in my area' or 'Tomato prices near Pune'.\n"
            "- You can also ask about irrigation, fertilizer timing, or disease prevention and I'll use available data.\n"
            "\nTL;DR: Ask a weather or market question for specific, data-backed advice."
        )

    if intent == "weather":
        weather = next((t.get("output", {}) for t in tools_used if t.get("name") == "weather"), {})
        daily = weather.get("daily") or []
        summary = weather.get("summary") or weather.get("desc")
        lines: List[str] = []
        if summary:
            lines.append(f"Forecast summary: {summary}.")
        if daily:
            day = daily[0]
            tmin = day.get("tmin") or day.get("min")
            tmax = day.get("tmax") or day.get("max")
            rain = day.get("rain") or day.get("precip")
            segs = []
            if tmin is not None and tmax is not None:
                segs.append(f"{tmin}–{tmax}°C")
            if rain is not None:
                segs.append(f"rain {rain} mm")
            if segs:
                lines.append("Today: " + ", ".join(segs) + ".")
        if not lines:
            lines.append("Here's the upcoming weather based on available data.")
        lines.append("\nAdvice: Irrigate only if topsoil is dry and there's low rain probability. Adjust fertilizer if heavy rain is forecast.")
        lines.append("TL;DR: Use the next 2–3 day outlook to time irrigation and inputs.")
        return "\n".join(lines)

    if intent == "market":
        market = next((t.get("output", {}) for t in tools_used if t.get("name") == "market"), {})
        price = market.get("price") or market.get("modal_price") or market.get("average")
        loc = market.get("market") or market.get("district") or market.get("state")
        lines: List[str] = []
        if price is not None and loc:
            lines.append(f"Latest price near {loc}: {price}.")
        elif price is not None:
            lines.append(f"Latest price: {price}.")
        else:
            lines.append("Here are the latest market trends available.")
        trend = market.get("trend")
        if trend:
            lines.append(f"Trend: {trend}.")
        lines.append("\nAdvice: If prices are rising, consider phased sales; if falling, explore nearby markets or collective selling.")
        lines.append("TL;DR: Use current price and trend to time your sale.")
        return "\n".join(lines)

    # Safe default
    return "I generated guidance based on available data. Ask about weather or market to get specific recommendations."
