from __future__ import annotations
from typing import Any, Dict, List
import json
import os

from ..infra.settings import settings
from .prompts.response_composition import (
    SHETKARI_COMPOSER_SYSTEM_PROMPT,
    GEMINI_COMPOSER_PROMPT_TEMPLATE,
    FALLBACK_RESPONSES
)

# Gemini LLM (optional)
try:
    import google.generativeai as genai  # type: ignore
    _GEMINI_AVAILABLE = True
except Exception:  # pragma: no cover
    _GEMINI_AVAILABLE = False


def _gemini_client():
    if not settings.gemini_api_key or not _GEMINI_AVAILABLE:
        return None
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def compose_answer(tools_used: List[Dict[str, Any]], intent: str, locale: str | None = None) -> Dict[str, Any]:
    """Compose final answer. Falls back to deterministic template if no LLM key.

    Returns dict with {text, citations}
    """
    # Remove citations processing as requested by user
    citations: List[Dict[str, Any]] = []

    # If Gemini is available, use it to craft natural text constrained to tools
    client = _gemini_client()
    if client:
        tool_summaries = json.dumps({t["name"]: t.get("output", {}) for t in tools_used})
        prompt = GEMINI_COMPOSER_PROMPT_TEMPLATE.format(
            system_prompt=SHETKARI_COMPOSER_SYSTEM_PROMPT,
            intent=intent,
            locale=locale or 'en-IN',
            tool_summaries=tool_summaries
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
            "- You can also ask about irrigation, fertilizer timing, or disease prevention and I'll use available data."
        )

    if intent == "weather":
        # Handle new weather tool format with 4 specialized tools
        weather_tool = next((t for t in tools_used if t.get("name", "").startswith("get_")), {})
        tool_name = weather_tool.get("name", "")
        weather_output = weather_tool.get("output", {})
        
        if not weather_output.get("success", False):
            return f"Weather data unavailable: {weather_output.get('error', 'Unknown error')}"
        
        lines: List[str] = []
        data = weather_output.get("data", {})
        
        # Handle current weather tool
        if tool_name == "get_current_weather":
            temp = data.get("temperature_celsius")
            humidity = data.get("humidity_percent") 
            soil_temp = data.get("soil_temperature_celsius")
            soil_moisture = data.get("soil_moisture_percent")
            precip = data.get("precipitation_mm", 0)
            
            conditions = []
            if temp is not None:
                conditions.append(f"{temp:.1f}°C")
            if humidity is not None:
                conditions.append(f"{humidity:.0f}% humidity")
            if precip > 0:
                conditions.append(f"{precip:.1f}mm rain")
                
            lines.append(f"Current conditions: {', '.join(conditions)}.")
            
            if soil_temp is not None and soil_moisture is not None:
                lines.append(f"Soil: {soil_temp:.1f}°C, {soil_moisture:.1f}% moisture.")
            
            # Agricultural advice based on current conditions
            advice = []
            if precip > 5:
                advice.append("Avoid spraying pesticides due to rain")
            elif soil_moisture and soil_moisture < 30:
                advice.append("Consider irrigation - soil moisture is low")
            elif humidity and humidity > 80:
                advice.append("High humidity - monitor for fungal diseases")
                
            if advice:
                lines.append(f"Advice: {'. '.join(advice)}.")
        
        # Handle future weather tool  
        elif tool_name == "get_future_weather":
            forecast = data.get("daily_forecast", [])
            if forecast:
                days_shown = min(3, len(forecast))
                for i, day in enumerate(forecast[:days_shown]):
                    date = day.get("date", "")
                    tmax = day.get("max_temp_celsius")
                    tmin = day.get("min_temp_celsius")
                    rain = day.get("precipitation_mm", 0)
                    
                    day_parts = []
                    if tmax is not None and tmin is not None:
                        day_parts.append(f"{tmin:.0f}-{tmax:.0f}°C")
                    if rain > 0:
                        day_parts.append(f"{rain:.1f}mm rain")
                    else:
                        day_parts.append("no rain")
                        
                    day_name = "Today" if i == 0 else ("Tomorrow" if i == 1 else date.split('-')[2] if '-' in date else date)
                    lines.append(f"{day_name}: {', '.join(day_parts)}")
                
                # Planning advice
                total_rain = sum(day.get("precipitation_mm", 0) for day in forecast[:7])
                if total_rain > 50:
                    lines.append("Heavy rain expected - delay harvest and protect crops.")
                elif total_rain < 5:
                    lines.append("Dry period ahead - plan irrigation schedule.")
                else:
                    lines.append("Moderate conditions - good for most farm activities.")
        
        # Handle historical weather tool
        elif tool_name == "get_historical_weather":
            summary = data.get("summary", {})
            period = data.get("period", {})
            
            if summary:
                temp_summary = summary.get("temperature", {})
                rain_summary = summary.get("precipitation", {})
                
                if temp_summary:
                    avg_temp = temp_summary.get("avg_max_celsius")
                    if avg_temp is not None:
                        lines.append(f"Historical average: {avg_temp:.1f}°C max temperature.")
                
                if rain_summary:
                    total_rain = rain_summary.get("total_mm")
                    if total_rain is not None:
                        lines.append(f"Total rainfall in period: {total_rain:.0f}mm.")
                
                lines.append(f"Data period: {period.get('start', '')} to {period.get('end', '')}.")
                lines.append("Use this pattern to select suitable crop varieties for similar conditions.")
        
        # Handle weather alerts tool
        elif tool_name == "get_weather_alerts":
            alerts = data.get("alerts", [])
            alert_count = data.get("alert_count", 0)
            
            if alert_count == 0:
                lines.append("No active weather alerts in your area.")
                lines.append("Conditions are favorable for normal farm activities.")
            else:
                lines.append(f"⚠️ {alert_count} active weather alert(s):")
                for alert in alerts[:3]:  # Show max 3 alerts
                    event = alert.get("event", "Weather Alert")
                    severity = alert.get("severity", "medium")
                    severity_icon = "🚨" if severity == "high" else "⚠️"
                    lines.append(f"{severity_icon} {event}")
                
                if data.get("has_severe_alerts"):
                    lines.append("URGENT: Take immediate action to protect crops and livestock!")
                else:
                    lines.append("Monitor conditions and prepare protective measures.")
        
        # Default fallback
        if not lines:
            lines.append("Weather data retrieved successfully. Use for agricultural planning.")
        
        return "\n".join(lines)

    if intent == "govt_scheme":
        # Handle government policy agent responses
        policy_tool = next((t for t in tools_used if t.get("name") == "search_schemes"), {})
        policy_output = policy_tool.get("output", {})
        
        if not policy_output.get("success", False):
            return f"Government scheme information unavailable: {policy_output.get('error', 'Unknown error')}"
        
        data = policy_output.get("data", {})
        schemes_info = data.get("schemes_info", "")
        sources = policy_output.get("sources") or data.get("sources", [])
        structured = data.get("schemes_structured", [])
        
        lines = []
        # Prefer strict JSON format if available as requested by frontend/judges
        if structured:
            import json as _json
            lines.append("Here are the most relevant government schemes (max 5):")
            lines.append("\n```json")
            # Ensure max 5
            lines.append(_json.dumps(structured[:5], ensure_ascii=False, indent=2))
            lines.append("```")
        elif schemes_info:
            lines.append(schemes_info)
        
        # Citations removed as requested by user
        
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
        return "\n".join(lines)

    # Safe default
    return "I generated guidance based on available data. Ask about weather or market to get specific recommendations."
