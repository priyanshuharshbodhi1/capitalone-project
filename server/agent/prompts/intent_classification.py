"""
Intent Classification Prompts for Agricultural AI Assistant

This module contains all prompts related to intent detection and classification
for farming-related queries.
"""

GROQ_INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a farming assistant with specialized tools.
Allowed intents: {intents}.

AVAILABLE TOOLS:

1. get_current_weather - Real-time weather for irrigation/pesticide decisions
2. get_future_weather - Weather forecasts for crop planning
3. get_historical_weather - Historical patterns for crop selection  
4. get_weather_alerts - Weather warnings for crop protection
5. search_schemes - Government policies and subsidies
6. get_market_data - Crop prices and market information
7. diagnose_plant_disease - AI-powered plant disease diagnosis with treatment recommendations

INTENT CATEGORIES:
- weather: Current conditions, forecasts, historical data, alerts
- govt_scheme: Government schemes, subsidies, policies, regulations
- market: Crop prices, market rates, selling information
- agronomist: Crop advice, farming techniques, pest management, plant disease diagnosis
- IoT_info: Sensor data, smart farming technology
- general: Unclear or out-of-scope queries

If the query is unclear, incomplete, or you cannot determine the intent with confidence, classify as "general" and the system will ask for clarification.

Respond with ONLY a JSON object containing an "intents" array. No explanation or extra text.

Examples:
USER: Will it rain tomorrow?
{{"intents": ["weather"]}}

USER: Current soil moisture levels?
{{"intents": ["weather"]}}

USER: Government subsidy for drip irrigation?
{{"intents": ["govt_scheme"]}}

USER: Tomato prices in Maharashtra
{{"intents": ["market"]}}

USER: Best crop for clay soil with irregular rainfall?
{{"intents": ["weather", "agronomist"]}}

USER: Help me
{{"intents": ["general"]}}

USER: {user_text}"""

# Intent categories and keywords for heuristic fallback - expanded weather keywords for 4 tools
INTENT_KEYWORDS = {
    "weather": [
        # Current weather keywords
        "current", "now", "today", "right now", "irrigate", "spray", "pesticides", "soil moisture", "soil temperature",
        # Future weather keywords  
        "weather", "rain", "temperature", "forecast", "tomorrow", "next week", "will it", "planning", "when to plant",
        # Historical weather keywords
        "last year", "previous", "historical", "pattern", "compare", "suited", "monsoon", "season",
        # Alert keywords
        "alerts", "warnings", "storms", "emergency", "protect", "severe", "wind", "humid", "humidity", "sun"
    ],
    "market": ["price", "market", "mandi", "sell", "rate", "wholesale", "buyer", "auction"],
    "govt_scheme": ["policy", "government", "scheme", "subsidy", "loan", "credit", "regulation", "law"],
    "agronomist": ["crop", "suitable", "variety", "sowing", "planting", "yield", "irrigation", "fertilizer", "pest", "disease", "seed", "soil", "nutrition", "expert", "advice", "diagnose", "identify", "plant health", "symptoms", "treatment", "remedy", "infection", "fungus", "virus", "bacteria", "leaf", "spots", "wilting", "yellowing", "brown", "sick plant", "plant doctor"],
    "IoT_info": ["sensor", "iot", "device", "monitor", "data", "smart", "automation", "technology", "equipment"]
}

SUPPORTED_INTENTS = ["market", "weather", "govt_scheme", "agronomist", "IoT_info"]
