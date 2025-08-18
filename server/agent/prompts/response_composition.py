"""
Response Composition Prompts for Agricultural AI Assistant

This module contains all prompts related to generating final responses
based on tool outputs and user intents.
"""

SHETKARI_COMPOSER_SYSTEM_PROMPT = """You are Shetkari's Answer Composer. You MUST produce a helpful, concise advisory ONLY using the provided tool outputs. Do not invent facts. Provide clear, actionable agricultural advice without TL;DR sections or citations."""

GEMINI_COMPOSER_PROMPT_TEMPLATE = """{system_prompt}

Intent: {intent}. Locale: {locale}.
TOOL_RESULTS_JSON: {tool_summaries}
Compose a user-facing answer strictly from TOOL_RESULTS_JSON."""

# Fallback response templates for when LLM is not available
FALLBACK_RESPONSES = {
    "general": """I can help with farm weather and market prices.
- Ask things like: 'Weather for the next 3 days in my area' or 'Tomato prices near Pune'.
- You can also ask about irrigation, fertilizer timing, or disease prevention and I'll use available data.""",

    "weather": """Forecast summary: {summary}.
Today: {temp_range}, rain {rain_amount} mm.

Advice: Irrigate only if topsoil is dry and there's low rain probability. Adjust fertilizer if heavy rain is forecast.""",

    "market": """Latest price near {location}: {price}.
Trend: {trend}.

Advice: If prices are rising, consider phased sales; if falling, explore nearby markets or collective selling.""",

    "default": "I generated guidance based on available data. Ask about weather or market to get specific recommendations."
}
