"""
Intent Classification Prompts for Agricultural AI Assistant

This module contains all prompts related to intent detection and classification
for farming-related queries.
"""

GEMINI_INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a farming assistant with specialized weather tools.
Allowed intents: {intents}.

WEATHER TOOLS AVAILABLE (following OpenAI tool calling format):

1. get_current_weather
   - Parameters: lat (float), lon (float)
   - Use for: Real-time irrigation decisions, pesticide timing, current soil conditions
   - Response: temperature, humidity, precipitation, soil_temperature, soil_moisture
   - Keywords: "now", "current", "today", "right now", "should I irrigate", "spray pesticides"

2. get_future_weather  
   - Parameters: lat (float), lon (float), days (int, max=16)
   - Use for: Crop planning, planting timing, harvest scheduling
   - Response: daily forecasts with min/max temp, precipitation
   - Keywords: "tomorrow", "next week", "forecast", "will it rain", "planning", "when to plant"

3. get_historical_weather
   - Parameters: lat (float), lon (float), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
   - Use for: Crop variety selection, seasonal analysis, yield comparison
   - Response: historical temp/precipitation patterns with statistics
   - Keywords: "last year", "previous season", "historical", "pattern", "compare", "suited"

4. get_weather_alerts
   - Parameters: lat (float), lon (float)
   - Use for: Emergency planning, crop protection, storm warnings
   - Response: active alerts, severity levels, emergency notifications
   - Keywords: "alerts", "warnings", "storms", "emergency", "protect crops", "severe weather"

Classify user queries based on these specific weather tool capabilities.

Given the user text, output ONLY a compact JSON object with exactly one key 'intents' whose value is an array of relevant intents.
Multiple intents are allowed if the query spans multiple domains.
No extra text.

Examples:
USER: Will it rain tomorrow?
OUTPUT: {{"intents": ["weather"]}}
USER: What's the current soil moisture?
OUTPUT: {{"intents": ["weather"]}}
USER: Weather forecast for next 7 days
OUTPUT: {{"intents": ["weather"]}}
USER: Historical rainfall patterns last monsoon
OUTPUT: {{"intents": ["weather"]}}
USER: Any weather alerts for my area?
OUTPUT: {{"intents": ["weather"]}}
USER: Tomato prices near Nashik
OUTPUT: {{"intents": ["market"]}}
USER: What seed variety suits this unpredictable weather?
OUTPUT: {{"intents": ["weather", "agronomist"]}}
USER: {user_text}
OUTPUT:"""

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
    "govt_policy": ["policy", "government", "scheme", "subsidy", "loan", "credit", "regulation", "law"],
    "agronomist": ["crop", "suitable", "variety", "sowing", "planting", "yield", "irrigation", "fertilizer", "pest", "disease", "seed", "soil", "nutrition", "expert", "advice"],
    "IoT_info": ["sensor", "iot", "device", "monitor", "data", "smart", "automation", "technology", "equipment"]
}

SUPPORTED_INTENTS = ["market", "weather", "govt_policy", "agronomist", "IoT_info"]
