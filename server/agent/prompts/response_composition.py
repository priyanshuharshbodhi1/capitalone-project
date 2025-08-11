"""
Response Composition Prompts for Agricultural AI Assistant

This module contains all prompts related to generating final responses
based on tool outputs and user intents.
"""

SHETKARI_COMPOSER_SYSTEM_PROMPT = """You are Shetkari's Answer Composer. You MUST produce a helpful, concise advisory ONLY using the provided tool outputs. Do not invent facts. Always include a TL;DR and numbered steps. End with citations array."""

GEMINI_COMPOSER_PROMPT_TEMPLATE = """{system_prompt}

Intent: {intent}. Locale: {locale}.
TOOL_RESULTS_JSON: {tool_summaries}
Compose a user-facing answer strictly from TOOL_RESULTS_JSON."""

# Fallback response templates for when LLM is not available
FALLBACK_RESPONSES = {
    "general": """I can help with farm weather and market prices.
- Ask things like: 'Weather for the next 3 days in my area' or 'Tomato prices near Pune'.
- You can also ask about irrigation, fertilizer timing, or disease prevention and I'll use available data.

TL;DR: Ask a weather or market question for specific, data-backed advice.""",

    "weather": """Forecast summary: {summary}.
Today: {temp_range}, rain {rain_amount} mm.

Advice: Irrigate only if topsoil is dry and there's low rain probability. Adjust fertilizer if heavy rain is forecast.
TL;DR: Use the next 2–3 day outlook to time irrigation and inputs.""",

    "market": """Latest price near {location}: {price}.
Trend: {trend}.

Advice: If prices are rising, consider phased sales; if falling, explore nearby markets or collective selling.
TL;DR: Use current price and trend to time your sale.""",

    "default": "I generated guidance based on available data. Ask about weather or market to get specific recommendations."
}
